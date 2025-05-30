# Heimdall - Authentication and Authorization Service for Asgard

**Heimdall** is Asgard's authentication and authorization service, built atop [Keycloak](https://www.keycloak.org). Heimdall is responsible for managing users, organizations, client applications, and issuing secure tokens for all services and APIs in the distributed Asgard platform.



## Key Features

- **OpenID Connect (OIDC) & OAuth 2.0:**  
  Modern authentication for both users and services via industry standards.

- **Multi-Organization (Multi-Tenancy) Support:**  
  Organizations are enabled, allowing seamless grouping and management of users and clients.

- **Custom Client Applications:**  
  Register and configure clients for both backend services and user-facing applications.

- **Rich Token Claims:**  
  Custom mappers ensure user and organization data is available to services via OIDC claims.

- **Integration with Kong/Bifrost:**  
  Designed to work with the [Kong OIDC plugin](https://github.com/revomatico/kong-oidc) at the API gateway layer.



## Customizations in Asgard's Keycloak Realm

The following customizations have been made to the default Keycloak realm configuration for Asgard:

### 1. Created Two Clients

- **bifrost**  
  - Purpose: Used by the Bifrost API gateway for token validation and secured service communication.
  - Location: [bifrost client settings](http://localhost:8000/heimdall/admin/master/console/#/asgard/clients/e71ab6f4-4f1a-44ff-add1-a02aa4fa2ba4/settings)

- **asgard-ui**  
  - Purpose: Used by the frontend UI to authenticate users and call protected APIs.
  - Location: [asgard-ui client settings](http://localhost:8000/heimdall/admin/master/console/#/asgard/clients/96278a13-23b4-4a7e-a097-7301e887b047/settings)


### 2. Added `user_id` Mapper to Client Scope `profile`

- The `profile` client scope now includes a `user_id` claim in tokens.
- This allows downstream services and APIs to easily identify the authenticated user.
- See: [profile client scope mappers](http://localhost:8000/heimdall/admin/master/console/#/asgard/client-scopes/d0bbfb37-9c46-48ee-916f-4845133fa329/mappers)

### 3. Whitelisting Trusted Hosts for Client Registration

To allow client registration from specific domains, you must add your trusted host domains to the **Trusted Hosts Policy**:

- Go to **Trusted Hosts Policy** for anonymous client registration:  
  [http://localhost:8000/heimdall/admin/master/console/#/asgard/clients/client-registration/anonymous/trusted-hosts/42cf728c-339a-46eb-a463-f714dd10299d](http://localhost:8000/heimdall/admin/master/console/#/asgard/clients/client-registration/anonymous/trusted-hosts/42cf728c-339a-46eb-a463-f714dd10299d)
- Add the allowed domains in the list.  
- Only clients registering from these hosts will be accepted.



## Main Endpoints

- `/heimdall/`  
  Main API gateway path for Heimdall (proxied via Bifrost/Kong).

- `/heimdall/realms/asgard/.well-known/openid-configuration`  
  OIDC discovery endpoint; used by Bifrost, OdinMCP, and frontend clients.

- `/heimdall/realms/asgard/protocol/openid-connect/token/introspect`  
  Token introspection endpoint; used for validating access tokens.



## How Heimdall Works in Asgard

1. **User or Service Requests Access:**  
   Users log in via the UI (asgard-ui client) or backend services authenticate via Bifrost (bifrost client).

2. **Token Issuance:**  
   Heimdall (Keycloak) issues OIDC tokens containing organization and user claims.

3. **Token Validation:**  
   Bifrost validates tokens using the OIDC discovery and introspection endpoints.

4. **Claims Propagation:**  
   All downstream Asgard services (OdinMCP, Hermod, etc.) receive organization and user_id claims from Heimdall tokens for authorization and context.



## Admin Console

Access the Keycloak admin console at:  
[http://localhost:8000/heimdall/](http://localhost:8000/heimdall/)

- Default admin credentials (change immediately after setup!):
  - **Username:** `admin`
  - **Password:** `adminpassword`



## Security Notes

- **Always change default admin credentials before production use.**
- **Client secrets for bifrost, asgard-ui, and other clients must be strong and kept secure.**
- **Deploy Heimdall behind HTTPS in production.**
- **For client registration, only whitelisted (trusted) domains will be accepted.**



## References

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [Kong OIDC Plugin](https://github.com/revomatico/kong-oidc)
- [OIDC Spec](https://openid.net/connect/)
- [OAuth 2.0 Spec](https://oauth.net/2/)
