Example for customValues.yaml

```yaml
config:
  redis_input:
    host: redis
    port: 6379
    stream_ids: 
      - stream1
    stream_prefix: anomalydetection
  http_output:                                  # HTTP output settings (disabled if not defined)
    target_endpoint: http://HOST:PORT/ai-cockpit/api/decision
    module_name: MODULE_NAME
    minio:
      endpoint: "HOST:PORT"
      secure: True
      bucket_name: BUCKET_NAME
      user: USERNAME
      password: PASSWORD
    # auth:                                     # Uncomment to enable authentication
    #   token_endpoint_url: TOKEN_URL
    #   client_id: CLIENT_ID
    #   username: USERNAME
    #   password: PASSWORD
  # local_output:                               # Uncomment to enable local output (do not change the path, it is where the PV is mounted)
  #   path: /anomaly-data

```