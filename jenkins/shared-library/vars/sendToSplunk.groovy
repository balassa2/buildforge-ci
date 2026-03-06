import com.buildforge.PipelineConfig
import groovy.json.JsonOutput

/**
 * Send a structured build event directly to Splunk via HTTP Event Collector.
 * These are first-class business events (not log lines), so direct HEC
 * is the right pattern rather than relying on Fluent Bit log scraping.
 */
def call(PipelineConfig config, String eventType, Map extraFields = [:]) {
    def payload = [
        event: [
            type      : eventType,
            app       : config.appName,
            branch    : config.branch,
            image     : config.fullImageRef(),
            build_id  : env.BUILD_NUMBER,
            build_url : env.BUILD_URL,
            timestamp : new Date().format("yyyy-MM-dd'T'HH:mm:ss'Z'", TimeZone.getTimeZone('UTC'))
        ] + extraFields,
        sourcetype: 'buildforge:pipeline',
        index     : 'buildforge'
    ]

    def jsonBody = JsonOutput.toJson(payload)

    withCredentials([string(credentialsId: config.splunkHecCredentialId, variable: 'HEC_TOKEN')]) {
        httpRequest(
            url: config.splunkHecUrl,
            httpMode: 'POST',
            customHeaders: [[name: 'Authorization', value: "Splunk ${HEC_TOKEN}"]],
            requestBody: jsonBody,
            validResponseCodes: '200',
            quiet: true
        )
    }

    echo "Sent '${eventType}' event to Splunk for ${config.appName}"
}
