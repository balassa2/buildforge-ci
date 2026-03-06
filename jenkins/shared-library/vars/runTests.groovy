import com.buildforge.PipelineConfig

/**
 * Run pytest and publish JUnit-format results.
 * Jenkins will display test counts and trends on the build page.
 */
def call(PipelineConfig config) {
    echo "Running tests for ${config.appName}"

    sh """
        pip install pytest
        pytest tests/ \
            --junitxml=test-results.xml \
            -v
    """

    junit allowEmptyResults: true, testResults: 'test-results.xml'
}
