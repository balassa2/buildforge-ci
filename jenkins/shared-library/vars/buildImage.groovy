import com.buildforge.PipelineConfig

/**
 * Build a container image using Kaniko (no Docker daemon required).
 * Kaniko runs as a sidecar container in the Jenkins agent pod,
 * reads the Dockerfile from the workspace, and pushes directly to the registry.
 */
def call(PipelineConfig config) {
    echo "Building image: ${config.fullImageRef()}"

    container('kaniko') {
        sh """
            /kaniko/executor \
                --context=\${WORKSPACE} \
                --dockerfile=\${WORKSPACE}/Dockerfile \
                --destination=${config.fullImageRef()} \
                --cache=true \
                --cache-ttl=24h
        """
    }

    echo "Image pushed: ${config.fullImageRef()}"
}
