package com.example.quizmaster.exception;

import com.example.quizmaster.dto.AuthDto;

import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.reactive.function.client.WebClientResponseException;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ApiException.class)
    public ResponseEntity<AuthDto.MessageResponse> handleApiException(ApiException ex) {
        return new ResponseEntity<>(new AuthDto.MessageResponse(ex.getMessage()), ex.getStatus());
    }

    @ExceptionHandler(WebClientResponseException.class)
    public ResponseEntity<AuthDto.MessageResponse> handleWebClientException(WebClientResponseException ex) {
        // Forward the status code from Keycloak (or other external services)
        return new ResponseEntity<>(new AuthDto.MessageResponse(ex.getResponseBodyAsString()), ex.getStatusCode());
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<AuthDto.MessageResponse> handleGeneralException(Exception ex) {
        return new ResponseEntity<>(new AuthDto.MessageResponse("An unexpected error occurred: " + ex.getMessage()),
                HttpStatus.INTERNAL_SERVER_ERROR);
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<Map<String, String>> handleAccessDenied(AccessDeniedException ex) {
        return ResponseEntity.status(HttpStatus.FORBIDDEN)
                .body(Map.of("error", "Access Denied", "message", ex.getMessage()));
    }
}
