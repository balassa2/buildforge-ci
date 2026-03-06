import com.buildforge.PipelineConfig

/**
 * Run pylint on Python source code.
 * Fails the build if the score drops below the configured threshold.
 */
def call(PipelineConfig config) {
    echo "Running pylint for ${config.appName} (threshold: ${config.pylintThreshold}/10)"

    sh """
        pip install pylint
        pylint --fail-under=${config.pylintThreshold} \
               --output-format=text \
               --reports=y \
               app/ || true
    """

    // Parse pylint score from output for logging
    sh """
        SCORE=\$(pylint app/ --score=y 2>/dev/null | grep 'Your code has been rated' | \\
                 grep -oP '[0-9]+\\.[0-9]+' | head -1)
        echo "Pylint score: \${SCORE:-unknown}/10"
        if [ "\$(echo "\${SCORE:-0} < ${config.pylintThreshold}" | bc)" -eq 1 ]; then
            echo "FAIL: Pylint score \${SCORE} is below threshold ${config.pylintThreshold}"
            exit 1
        fi
    """
}
