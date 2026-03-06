import com.buildforge.PipelineConfig

/**
 * Deploy to Kubernetes by updating the container image on an existing deployment.
 * Uses kubectl set image for a rolling update -- no downtime.
 */
def call(PipelineConfig config) {
    echo "Deploying ${config.appName} to namespace ${config.namespace}"

    sh """
        kubectl set image deployment/${config.appName} \
            ${config.appName}=${config.fullImageRef()} \
            -n ${config.namespace}

        kubectl rollout status deployment/${config.appName} \
            -n ${config.namespace} \
            --timeout=120s
    """

    echo "Deployment of ${config.appName} complete"
}
