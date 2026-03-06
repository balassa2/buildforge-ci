package com.buildforge

/**
 * Holds configuration shared across all pipeline steps.
 * Instantiated once at the start of buildforgePipeline and passed to each stage.
 */
class PipelineConfig implements Serializable {
    private static final long serialVersionUID = 1L

    String appName
    String repoUrl
    String branch = 'main'
    String language = 'python'

    // Image settings
    String registry = 'ghcr.io/balassa2/buildforge-ci'
    String imageTag = 'latest'

    // Linting
    int pylintThreshold = 8

    // Kubernetes
    String namespace = 'buildforge'
    String manifestsPath = 'k8s/'

    // Splunk HEC for structured build events
    String splunkHecUrl = 'http://splunk.buildforge-monitoring:8088/services/collector/event'
    String splunkHecCredentialId = 'splunk-hec-token'

    /**
     * Full image reference for docker/kaniko push.
     * Example: ghcr.io/balassa2/buildforge-ci/myapp:abc123
     */
    String fullImageRef() {
        return "${registry}/${appName}:${imageTag}"
    }
}
