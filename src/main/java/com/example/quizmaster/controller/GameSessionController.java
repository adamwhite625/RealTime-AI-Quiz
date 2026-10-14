package com.example.quizmaster.controller;

import com.example.quizmaster.dto.GameSessionDto;
import com.example.quizmaster.entity.GameSession;
import com.example.quizmaster.entity.Player;
import com.example.quizmaster.repository.PlayerRepository;
import com.example.quizmaster.service.GameSessionService;
import jakarta.validation.Valid;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/sessions")
public class GameSessionController {

    private final GameSessionService gameSessionService;
    private final PlayerRepository playerRepository;

    @Autowired
    public GameSessionController(GameSessionService gameSessionService, PlayerRepository playerRepository) {
        this.gameSessionService = gameSessionService;
        this.playerRepository = playerRepository;
    }

    @PostMapping
    public ResponseEntity<GameSessionDto.CreateResponse> createSession(
            @Valid @RequestBody GameSessionDto.CreateRequest request,
            @AuthenticationPrincipal Jwt jwt) {
        // 1. Extract User ID (subject) from the JWT token
        String userId = jwt.getSubject();

        // 2. Call Service to create the session
        // (Service handles the logic: Is it Public? Is User the Creator?)
        GameSession session = gameSessionService.createSession(request.getQuizId(), userId);

        // 3. Map Entity to DTO Response
        GameSessionDto.CreateResponse response = GameSessionDto.CreateResponse.from(session);

        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @PostMapping("/{sessionId}/start")
    public ResponseEntity<GameSessionDto.CreateResponse> startSession(
            @PathVariable String sessionId,
            @AuthenticationPrincipal Jwt jwt) {
        String userId = jwt.getSubject();
        GameSession session = gameSessionService.startGameSession(sessionId, userId);
        GameSessionDto.CreateResponse response = GameSessionDto.CreateResponse.from(session);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/{sessionId}/end")
    public ResponseEntity<GameSessionDto.CreateResponse> endSession(
            @PathVariable String sessionId,
            @AuthenticationPrincipal Jwt jwt) {
        String userId = jwt.getSubject();
        GameSession session = gameSessionService.endGameSession(sessionId, userId);
        GameSessionDto.CreateResponse response = GameSessionDto.CreateResponse.from(session);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/join")
    public ResponseEntity<GameSessionDto.JoinResponse> joinSession(
            @Valid @RequestBody GameSessionDto.JoinRequest request) {

        // Note: Joining usually doesn't require JWT (AuthenticationPrincipal)
        // because players are often anonymous guests.

        Player newPlayer = gameSessionService.joinSession(request.getGamePin(), request.getNickname());

        List<Player> allPlayers = playerRepository.findByGameSessionId(newPlayer.getGameSession().getId());

        List<GameSessionDto.PlayerInfo> playerList = allPlayers.stream()
                .map(p -> new GameSessionDto.PlayerInfo(p.getId(), p.getNickname()))
                .toList();

        GameSessionDto.JoinResponse response = new GameSessionDto.JoinResponse(
                newPlayer.getId(),
                newPlayer.getNickname(),
                newPlayer.getGameSession().getId(),
                playerList);

        return ResponseEntity.ok(response);
    }

    @PostMapping("/{sessionId}/players/{playerId}/leave")
    public ResponseEntity<Void> leaveSession(
            @PathVariable String sessionId,
            @PathVariable Long playerId) {

        // Note: No JWT check here allows players to leave on their own.
        // If you want "Kick" functionality (Host only), you would check JWT here.

        gameSessionService.removePlayer(sessionId, playerId);

        return ResponseEntity.noContent().build();
    }
}