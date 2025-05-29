FROM quay.io/keycloak/keycloak:26.1.4 as keycloak-builder

ENV KC_DB=postgres

# Build Keycloak without runtime-only parameters
RUN /opt/keycloak/bin/kc.sh build --health-enabled=true \
    --features=preview \
    --verbose

FROM quay.io/keycloak/keycloak:26.1.4

# Copy Keycloak built artifacts from the keycloak-builder stage
COPY --from=keycloak-builder /opt/keycloak/lib/quarkus/ /opt/keycloak/lib/quarkus/
COPY --from=keycloak-builder /opt/keycloak/providers/ /opt/keycloak/providers/

ENV KC_DB=postgres

# Define the entrypoint for Keycloak with all runtime flags
ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]