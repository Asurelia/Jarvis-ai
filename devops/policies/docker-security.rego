# Docker Security Policy for JARVIS AI
# Validates Docker Compose configurations for security compliance

package docker.security

# Deny running containers as root
deny[msg] {
    input.services[service_name].user == "root"
    msg := sprintf("Service '%s' should not run as root user", [service_name])
}

# Require security_opt settings
deny[msg] {
    not input.services[service_name].security_opt
    msg := sprintf("Service '%s' must define security_opt", [service_name])
}

# Require no-new-privileges
deny[msg] {
    service := input.services[service_name]
    service.security_opt
    not "no-new-privileges:true" in service.security_opt
    msg := sprintf("Service '%s' must set no-new-privileges:true", [service_name])
}

# Deny privileged containers
deny[msg] {
    input.services[service_name].privileged == true
    msg := sprintf("Service '%s' should not run in privileged mode", [service_name])
}

# Require resource limits
deny[msg] {
    not input.services[service_name].deploy.resources.limits
    msg := sprintf("Service '%s' must define resource limits", [service_name])
}

# Deny binding to 0.0.0.0 in production
deny[msg] {
    contains(input.services[service_name].ports[_], "0.0.0.0:")
    msg := sprintf("Service '%s' should not bind to 0.0.0.0 in production", [service_name])
}

# Require health checks for critical services
critical_services := ["brain-api", "postgres-prod", "redis-prod"]

deny[msg] {
    service_name in critical_services
    not input.services[service_name].healthcheck
    msg := sprintf("Critical service '%s' must define health checks", [service_name])
}

# Require read-only filesystem where possible
deny[msg] {
    service_name in ["brain-api", "tts-service", "stt-service"]
    input.services[service_name].read_only != true
    msg := sprintf("Service '%s' should use read-only filesystem", [service_name])
}

# Validate secret management
deny[msg] {
    contains(input.services[service_name].environment[_], "PASSWORD=")
    msg := sprintf("Service '%s' should not have plaintext passwords in environment", [service_name])
}

# Require restart policies
deny[msg] {
    not input.services[service_name].restart
    not input.services[service_name].deploy.restart_policy
    msg := sprintf("Service '%s' must define restart policy", [service_name])
}