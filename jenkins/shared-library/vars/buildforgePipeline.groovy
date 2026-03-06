import com.buildforge.PipelineConfig

/**
 * Opinionated full CI/CD pipeline for BuildForge applications.
 * Teams call this from their Jenkinsfile with a config closure.
 *
 * Usage:
 *   buildforgePipeline {
 *       appName   = 'my-service'
 *       repoUrl   = 'https://github.com/balassa2/my-service'
 *       branch    = 'main'
 *       language  = 'python'
 *   }
 */
def call(Closure body) {
    def config = new PipelineConfig()
    body.delegate = config
    body.resolveStrategy = Closure.DELEGATE_FIRST
    body()

    // Use the short git SHA as the image tag for traceability
    config.imageTag = env.GIT_COMMIT?.take(7) ?: 'latest'

    pipeline {
        agent {
            kubernetes {
                yaml libraryResource('agent-pod-template.yaml')
            }
        }

        environment {
            APP_NAME = config.appName
            IMAGE_REF = config.fullImageRef()
        }

        stages {
            stage('Checkout') {
                steps {
                    checkout scm
                    sendToSplunk(config, 'build_started', [stage: 'checkout'])
                }
            }

            stage('Lint') {
                steps {
                    runLinting(config)
                }
            }

            stage('Test') {
                steps {
                    runTests(config)
                }
            }

            stage('Build Image') {
                steps {
                    buildImage(config)
                }
            }

            stage('Deploy') {
                when {
                    branch 'main'
                }
                steps {
                    deployToK8s(config)
                }
            }
        }

        post {
            success {
                sendToSplunk(config, 'build_completed', [result: 'SUCCESS'])
            }
            failure {
                sendToSplunk(config, 'build_failed', [result: 'FAILURE'])
            }
        }
    }
}
