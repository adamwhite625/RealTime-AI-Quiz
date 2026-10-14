package com.example.quizmaster.service;

import com.example.quizmaster.dto.AuthDto;
import com.example.quizmaster.exception.ApiException;
import com.example.quizmaster.repository.UserRepository;

import org.keycloak.admin.client.CreatedResponseUtil;
import org.keycloak.admin.client.Keycloak;
import org.keycloak.admin.client.KeycloakBuilder;
import org.keycloak.OAuth2Constants;
import org.keycloak.representations.AccessTokenResponse;
import org.keycloak.representations.idm.CredentialRepresentation;
import org.keycloak.representations.idm.UserRepresentation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

import jakarta.ws.rs.NotAuthorizedException;
import jakarta.ws.rs.core.Response;
import java.util.Collections;

@Service
public class UserService {

    @Autowired
    private UserRepository userRepository; // Your local Postgres repo

    @Autowired
    private Keycloak keycloak; // Inject the Bean (see config below)

    @Value("${keycloak.realm}")
    private String realm;
    @Value("${keycloak.auth-server-url}")
    private String serverUrl;
    @Value("${keycloak.resource}")
    private String clientId;
    @Value("${keycloak.credentials.secret}")
    private String clientSecret;

    public AuthDto.MessageResponse register(AuthDto.SignUpRequest request) {
        // 1. PREPARE KEYCLOAK USER OBJECT
        UserRepresentation kcUser = new UserRepresentation();
        kcUser.setEnabled(true);
        kcUser.setUsername(request.getEmail());
        kcUser.setEmail(request.getEmail());
        kcUser.setFirstName(request.getFirstName());
        kcUser.setLastName(request.getLastName());
        kcUser.setEmailVerified(true);

        CredentialRepresentation credential = new CredentialRepresentation();
        credential.setType(CredentialRepresentation.PASSWORD);
        credential.setValue(request.getPassword());
        credential.setTemporary(false);
        kcUser.setCredentials(Collections.singletonList(credential));

        // 2. CALL KEYCLOAK API (Writes to 'keycloak_db')
        Response response = keycloak.realm(realm).users().create(kcUser);

        if (response.getStatus() == 201) {
            // 3. EXTRACT THE NEW ID (CRITICAL STEP)
            // Keycloak returns the ID in the Location header, usually the last part of the
            // path
            String userId = CreatedResponseUtil.getCreatedId(response);

            // 4. SAVE TO LOCAL DATABASE (Writes to 'quizmaster' db)
            // This ensures your local DB has the ID to link with Quiz Results later
            com.example.quizmaster.entity.User localUser = new com.example.quizmaster.entity.User();
            localUser.setId(userId); // SYNC THE ID!
            localUser.setEmail(request.getEmail());
            localUser.setFirstName(request.getFirstName());
            localUser.setLastName(request.getLastName());

            try {
                userRepository.save(localUser);
            } catch (Exception e) {
                // COMPENSATION LOGIC:
                // If local save fails, you should delete the user from Keycloak
                // to prevent "Ghost Users" (exists in Auth but not in App).
                keycloak.realm(realm).users().get(userId).remove();
                throw new RuntimeException("Local database error. Registration rolled back.");
            }

            return new AuthDto.MessageResponse("User registered successfully");

        } else if (response.getStatus() == 409) {
            throw new ApiException("User already exists", HttpStatus.CONFLICT);
        } else {
            throw new ApiException("Failed to register user", HttpStatus.valueOf(response.getStatus()));
        }
    }

    public AuthDto.LoginResponse login(AuthDto.LoginRequest request) {
        try {
            // 1. Create a Keycloak instance specifically for this authentication attempt
            // We use the "PASSWORD" grant type here to exchange creds for a token
            Keycloak keycloakUser = KeycloakBuilder.builder()
                    .serverUrl(serverUrl)
                    .realm(realm)
                    .clientId(clientId)
                    .clientSecret(clientSecret) // Required if your client is 'Confidential'
                    .grantType(OAuth2Constants.PASSWORD)
                    .username(request.getEmail())
                    .password(request.getPassword())
                    .build();

            // 2. Request the token
            // access() or tokenManager().getAccessToken() triggers the HTTP call
            AccessTokenResponse tokenResponse = keycloakUser.tokenManager().getAccessToken();

            // 3. Map Keycloak response to your custom response
            return new AuthDto.LoginResponse(
                    tokenResponse.getToken(),
                    tokenResponse.getRefreshToken(),
                    tokenResponse.getExpiresIn(),
                    tokenResponse.getTokenType());

        } catch (NotAuthorizedException e) {
            // 4. Handle Bad Credentials (401)
            throw new com.example.quizmaster.exception.ApiException(
                    "Invalid email or password",
                    org.springframework.http.HttpStatus.UNAUTHORIZED);
        } catch (Exception e) {
            // 5. Handle other errors (Keycloak down, timeouts, etc.)
            throw new com.example.quizmaster.exception.ApiException(
                    "Login failed: " + e.getMessage(),
                    org.springframework.http.HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // Change return type from 'User' to 'UserProfileDto'
    public com.example.quizmaster.dto.UserProfileDto getUserById(String id) {
        // 1. Fetch the Entity
        com.example.quizmaster.entity.User user = userRepository.findById(id)
                .orElseThrow(() -> new com.example.quizmaster.exception.ApiException(
                        "User not found",
                        org.springframework.http.HttpStatus.NOT_FOUND));

        // 2. Map Entity to DTO (Only select the fields you want)
        return new com.example.quizmaster.dto.UserProfileDto(
                user.getId(),
                user.getEmail(),
                user.getFirstName(),
                user.getLastName());
    }
}
