/*
 * Example Jenkinsfile for a Python application using the BuildForge shared library.
 * This is what an app team's Jenkinsfile looks like -- roughly 10 lines.
 * The shared library handles all the stages: lint, test, build image, deploy.
 */

@Library('buildforge-shared-library') _

buildforgePipeline {
    appName   = 'demo-app'
    repoUrl   = 'https://github.com/balassa2/demo-app'
    branch    = env.BRANCH_NAME ?: 'main'
    language  = 'python'
    namespace = 'buildforge'
}
