package com.example.quizmaster.controller;

import com.example.quizmaster.dto.AnswerSubmissionDto;
import com.example.quizmaster.dto.LeaderboardEntryDto;
import com.example.quizmaster.service.GameSessionService;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/sessions")
public class GameplayController {

    private final GameSessionService gameSessionService;

    @Autowired
    public GameplayController(GameSessionService gameSessionService) {
        this.gameSessionService = gameSessionService;
    }

    @PostMapping("/{sessionId}/next-question")
    public ResponseEntity<Void> nextQuestion(
            @PathVariable String sessionId,
            @AuthenticationPrincipal Jwt jwt) {
        String userId = jwt.getSubject();
        gameSessionService.sendNextQuestion(sessionId, userId);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/{sessionId}/submit-answer")
    public ResponseEntity<AnswerSubmissionDto.Response> submitAnswer(
            @PathVariable String sessionId,
            @RequestBody AnswerSubmissionDto.Request request // Using the nested class
    ) {

        AnswerSubmissionDto.Response response = gameSessionService.submitAnswer(sessionId, request);

        return ResponseEntity.ok(response);
    }

    @PostMapping("/{sessionId}/reveal-answer")
    public ResponseEntity<Void> revealAnswer(
            @PathVariable String sessionId,
            @AuthenticationPrincipal Jwt jwt) {
        gameSessionService.revealAnswer(sessionId, jwt.getSubject());
        return ResponseEntity.ok().build();
    }

    @GetMapping("/{sessionId}/leaderboard")
    public ResponseEntity<List<LeaderboardEntryDto>> getLeaderboard(@PathVariable String sessionId) {
        return ResponseEntity.ok(gameSessionService.getLeaderboard(sessionId));
    }
}