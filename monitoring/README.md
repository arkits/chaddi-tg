# Monitoring Chaddi

## Intro

Chaddi uses Prometheus to export metrics related to the application run-time and performance. The Bot has been instrumented to capture relevant details.

## Collecting metrics from Chaddi

### Enable the metrics endpoint in Chaddi

Update your `config.json` with the following metrics related configs - 

```json
"metrics": {
    "enabled": true,
    "port": 4208
}
```

### Proxy from Nginx

Depending on your setup, you may have to expose the metrics endpoint to the internet via Nginx. Here is a sample Nginx snippet to proxy an incoming request to the Chaddi's port.

```
location /chaddi/metrics {
    if ($request_uri ~* "/chaddi/metrics(.*)") {
            proxy_pass http://127.0.0.1:4208$1;
    }
}
```

You may optional add Basic Authentication from within Nginx using htpasswd. 