package com.example.quizmaster.controller;

import com.example.quizmaster.dto.QuizDto;
import com.example.quizmaster.dto.QuizSummaryDto;
import com.example.quizmaster.entity.Quiz;
import com.example.quizmaster.service.QuizService;

import jakarta.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;
import org.springframework.data.domain.Page;

@RestController
@RequestMapping("/api/quizzes")
public class QuizController {

    @Autowired
    private QuizService quizService;

    @GetMapping("/public") // No authentication needed usually, or permitAll()
    public ResponseEntity<Page<QuizSummaryDto>> getAllPublicQuizzes(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {

        return ResponseEntity.ok(quizService.getPublicQuizzes(page, size));
    }

    @PostMapping
    public ResponseEntity<?> createQuiz(
            @AuthenticationPrincipal Jwt jwt,
            @Valid @RequestBody QuizDto.CreateRequest request) {

        // 1. Extract User ID from Keycloak Token
        String userId = jwt.getSubject();

        // 2. Call Service
        Quiz createdQuiz = quizService.createQuiz(request, userId);

        // 3. Return Response (Returning ID is usually enough)
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(java.util.Map.of(
                        "message", "Quiz created successfully",
                        "id", createdQuiz.getId()));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteQuiz(
            @PathVariable String id,
            @AuthenticationPrincipal Jwt jwt) {

        // 1. Get the authenticated user's ID
        String userId = jwt.getSubject();

        // 2. Attempt to delete
        quizService.deleteQuiz(id, userId);

        // 3. Return 204 No Content (Standard for successful deletions)
        return ResponseEntity.noContent().build();
    }
}
