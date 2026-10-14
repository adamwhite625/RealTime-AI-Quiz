package com.example.quizmaster.service;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.Random;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.http.HttpStatus;
import org.springframework.messaging.simp.SimpMessagingTemplate;

import com.example.quizmaster.constants.SessionStatus;
import com.example.quizmaster.dto.AnswerSubmissionDto;
import com.example.quizmaster.dto.LeaderboardEntryDto;
import com.example.quizmaster.dto.PlayerDto;
import com.example.quizmaster.dto.QuestionBroadcastDto;
import com.example.quizmaster.dto.RevealAnswerDto;
import com.example.quizmaster.dto.SessionEventDto;
import com.example.quizmaster.exception.ApiException;
import com.example.quizmaster.entity.GameSession;
import com.example.quizmaster.entity.Option;
import com.example.quizmaster.entity.Player;
import com.example.quizmaster.entity.PlayerAnswer;
import com.example.quizmaster.entity.Question;
import com.example.quizmaster.entity.Quiz;
import com.example.quizmaster.repository.GameSessionRepository;
import com.example.quizmaster.repository.PlayerRepository;
import com.example.quizmaster.repository.QuizRepository;
import com.example.quizmaster.repository.PlayerAnswerRepository;
import com.example.quizmaster.repository.OptionRepository;

import jakarta.persistence.EntityNotFoundException;

@Service
public class GameSessionService {
    private final GameSessionRepository sessionRepository;
    private final QuizRepository quizRepository;
    private final PlayerRepository playerRepository;
    private final SimpMessagingTemplate messagingTemplate;
    private final PlayerAnswerRepository playerAnswerRepository;
    private final OptionRepository optionRepository;

    @Autowired
    public GameSessionService(GameSessionRepository sessionRepository, QuizRepository quizRepository,
            PlayerRepository playerRepository, SimpMessagingTemplate messagingTemplate,
            PlayerAnswerRepository playerAnswerRepository, OptionRepository optionRepository) {
        this.sessionRepository = sessionRepository;
        this.quizRepository = quizRepository;
        this.playerRepository = playerRepository;
        this.messagingTemplate = messagingTemplate;
        this.playerAnswerRepository = playerAnswerRepository;
        this.optionRepository = optionRepository;
    }

    @Transactional
    public GameSession createSession(String quizId, String userId) {
        // 1. Fetch the Quiz
        Quiz quiz = quizRepository.findById(quizId)
                .orElseThrow(() -> new EntityNotFoundException("Quiz not found"));

        // 2. Authorization Check
        // If quiz is NOT public, only the creator can host it
        if (!quiz.isPublic()) {
            // Assuming Creator has an ID field that matches the JWT subject (String)
            String creatorId = quiz.getCreator().getId().toString();
            if (!creatorId.equals(userId)) {
                throw new AccessDeniedException("You cannot host a private quiz that belongs to someone else.");
            }
        }

        // 3. Generate a unique 6-digit PIN
        String gamePin = generateUniquePin();

        // 4. Create and Save the Session
        GameSession session = new GameSession();
        session.setQuiz(quiz);
        session.setHostId(userId);
        session.setGamePin(gamePin);
        session.setStatus(SessionStatus.WAITING_FOR_PLAYERS);

        return sessionRepository.save(session);
    }

    @Transactional
    public GameSession startGameSession(String sessionId, String userId) {
        GameSession session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new EntityNotFoundException("Session not found"));

        if (!session.getHostId().equals(userId)) {
            throw new AccessDeniedException("Only the host can start the session");
        }

        // Idempotency check: If already in progress, just return it (don't crash)
        if (session.getStatus() == SessionStatus.IN_PROGRESS) {
            return session;
        }

        if (session.getStatus() != SessionStatus.WAITING_FOR_PLAYERS) {
            throw new ApiException("Cannot start session. Status is: " + session.getStatus(), HttpStatus.BAD_REQUEST);
        }

        session.setStatus(SessionStatus.IN_PROGRESS);
        GameSession savedSession = sessionRepository.save(session);

        // Broadcast "GAME_STARTED" event via WebSocket
        broadcastEvent(sessionId, "GAME_STARTED");

        return savedSession;
    }

    @Transactional
    public GameSession endGameSession(String sessionId, String userId) {
        GameSession session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new EntityNotFoundException("Session not found"));

        if (!session.getHostId().equals(userId)) {
            throw new AccessDeniedException("Only the host can end the session");
        }

        // Idempotency check
        if (session.getStatus() == SessionStatus.FINISHED) {
            return session;
        }

        session.setStatus(SessionStatus.FINISHED);
        GameSession savedSession = sessionRepository.save(session);

        // Broadcast "GAME_ENDED" event via WebSocket
        broadcastEvent(sessionId, "GAME_ENDED");

        return savedSession;
    }

    @Transactional
    public Player joinSession(String gamePin, String nickname) {
        // 1. Find Session by PIN
        GameSession session = sessionRepository.findByGamePin(gamePin)
                .orElseThrow(() -> new EntityNotFoundException("Game PIN not found"));

        // 2. Check Status (Can only join if WAITING)
        if (session.getStatus() != SessionStatus.WAITING_FOR_PLAYERS) {
            throw new ApiException("Game has already started or finished.", HttpStatus.BAD_REQUEST);
        }

        // 3. Check for Duplicate Nickname in this session
        if (playerRepository.existsByGameSessionAndNickname(session, nickname)) {
            throw new ApiException("Nickname '" + nickname + "' is already taken in this game.", HttpStatus.CONFLICT);
        }

        // 4. Create and Save Player
        Player player = new Player(nickname, session);
        Player savedPlayer = playerRepository.save(player);

        // 5. BROADCAST EVENT: Notify the Host (and everyone else in lobby)
        // Topic: /topic/session/{sessionId}/players
        String destination = "/topic/session/" + session.getId() + "/players";

        // We send a simple DTO or just the nickname
        // In a real app, define a specific "PlayerJoinedEvent" DTO
        PlayerDto.PlayerJoinedMessage message = new PlayerDto.PlayerJoinedMessage(nickname, savedPlayer.getId());
        messagingTemplate.convertAndSend(destination, message);

        return savedPlayer;
    }

    @Transactional
    public void removePlayer(String sessionId, Long playerId) {
        // 1. Find the Player
        Player player = playerRepository.findById(playerId)
                .orElseThrow(() -> new EntityNotFoundException("Player not found"));

        // 2. Validate they belong to the correct session
        if (!player.getGameSession().getId().equals(sessionId)) {
            throw new ApiException("Player " + playerId + " does not belong to session " + sessionId,
                    HttpStatus.BAD_REQUEST);
        }

        // 3. Capture details before deleting (for the notification)
        String nickname = player.getNickname();

        // 4. Delete from DB
        playerRepository.delete(player);

        // 5. BROADCAST EVENT: Notify everyone (Host + Players)
        // Payload: { "type": "PLAYER_LEFT", "playerId": 123, "nickname": "Mario" }
        String destination = "/topic/session/" + sessionId + "/players";

        PlayerDto.PlayerLeftMessage message = new PlayerDto.PlayerLeftMessage(nickname, playerId);
        messagingTemplate.convertAndSend(destination, message);
    }

    @Transactional
    public void sendNextQuestion(String sessionId, String userId) {
        // 1. Fetch Session
        GameSession session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new EntityNotFoundException("Session not found"));

        // 2. Authorization (Host only)
        if (!session.getHostId().equals(userId)) {
            throw new AccessDeniedException("Only host can control the game flow");
        }

        // 3. Get all questions from the Quiz
        List<Question> questions = session.getQuiz().getQuestions();
        int currentIndex = session.getCurrentQuestionIndex();

        // 4. Check if we ran out of questions
        if (currentIndex >= questions.size()) {
            throw new ApiException("No more questions available. Game should end.", HttpStatus.BAD_REQUEST);
            // Alternatively, you could auto-call endGameSession() here.
        }

        // 5. Get the current question
        Question question = questions.get(currentIndex);

        // 6. Map to Safe DTO (Stripping answers)
        List<QuestionBroadcastDto.OptionDto> safeOptions = question.getOptions().stream()
                .map(opt -> new QuestionBroadcastDto.OptionDto(opt.getId(), opt.getText(), opt.getOrderIndex()))
                .toList();

        QuestionBroadcastDto payload = new QuestionBroadcastDto(
                "NEXT_QUESTION",
                question.getId(),
                question.getText(),
                question.getTimeLimitSeconds(),
                currentIndex + 1, // Display number (1-based)
                questions.size(), // Total questions
                safeOptions);

        // Record the exact time we started this question
        session.setCurrentQuestionStartTime(LocalDateTime.now());

        // 7. Broadcast to WebSocket
        String destination = "/topic/session/" + sessionId + "/players";
        System.out.println(">>> BROADCASTING NEXT_QUESTION: " + question.getText());
        messagingTemplate.convertAndSend(destination, payload);

        // 8. Update State: Increment index for the NEXT call
        session.setCurrentQuestionIndex(currentIndex + 1);
        sessionRepository.save(session);
    }

    @Transactional
    public AnswerSubmissionDto.Response submitAnswer(String sessionId, AnswerSubmissionDto.Request request) {
        // 1. Validate Session & Player (Standard checks)
        GameSession session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new EntityNotFoundException("Session not found"));

        Player player = playerRepository.findById(request.getPlayerId())
                .orElseThrow(() -> new EntityNotFoundException("Player not found"));

        // 2. Get Current Question
        Question currentQuestion = session.getQuiz().getQuestions().get(session.getCurrentQuestionIndex() - 1);

        if (!currentQuestion.getId().equals(request.getQuestionId())) {
            throw new ApiException("Question mismatch.", HttpStatus.BAD_REQUEST);
        }

        // 3. Duplicate Check
        if (playerAnswerRepository.existsByPlayerAndQuestion(player, currentQuestion)) {
            throw new ApiException("You have already answered this question.", HttpStatus.CONFLICT);
        }

        // 4. Validate Option
        Option selectedOption = optionRepository.findById(request.getSelectedOptionId())
                .orElseThrow(() -> new EntityNotFoundException("Option not found"));

        // 5. Score Calculation Logic (Same as before)
        LocalDateTime now = LocalDateTime.now();
        long secondsElapsed = ChronoUnit.SECONDS.between(session.getCurrentQuestionStartTime(), now);

        // Timeout check (Buffer included)
        if (session.getCurrentQuestionStartTime() != null &&
                currentQuestion.getTimeLimitSeconds() != null &&
                secondsElapsed > (currentQuestion.getTimeLimitSeconds() + 2)) {
            throw new ApiException("Time limit exceeded", HttpStatus.BAD_REQUEST);
        }

        boolean isCorrect = selectedOption.isCorrect();
        int score = 0;

        if (isCorrect) {
            int maxPoints = currentQuestion.getPoints();
            if (currentQuestion.getTimeLimitSeconds() == null || currentQuestion.getTimeLimitSeconds() == 0) {
                score = maxPoints;
            } else {
                // Formula: Score = Max * (1 - (ResponseTime / TimeLimit) / 2)
                // This decays from 100% down to 50% as time runs out
                double decay = ((double) secondsElapsed / currentQuestion.getTimeLimitSeconds()) / 2.0;
                score = (int) (maxPoints * (1 - decay));
                // Safety clamp (can't be less than 50% if correct)
                if (score < maxPoints / 2)
                    score = maxPoints / 2;
            }
        }

        // 6. Save Answer
        PlayerAnswer answer = new PlayerAnswer();
        answer.setPlayer(player);
        answer.setQuestion(currentQuestion);
        answer.setSelectedOption(selectedOption);
        answer.setCorrect(isCorrect);
        answer.setScoreAwarded(score);
        playerAnswerRepository.save(answer);

        // Update Player Total Score
        if (score > 0) {
            player.setScore(player.getScore() + score);
            playerRepository.save(player);
        }

        // 7. BROADCAST TO HOST (Using DTO)
        int totalAnswers = playerAnswerRepository.countByQuestionAndSession(currentQuestion, sessionId);

        // Broadcast the correct count to the host
        AnswerSubmissionDto.HostUpdate hostUpdate = new AnswerSubmissionDto.HostUpdate(
                "ANSWER_RECEIVED",
                totalAnswers);
        messagingTemplate.convertAndSend("/topic/session/" + sessionId + "/host", hostUpdate);

        // 8. RETURN RESPONSE DTO (Using nested Response DTO)
        return new AnswerSubmissionDto.Response(
                isCorrect ? "Correct!" : "Incorrect",
                score,
                player.getScore(),
                isCorrect);
    }

    @Transactional
    public void revealAnswer(String sessionId, String userId) {
        // 1. Validate Session & Host
        GameSession session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new EntityNotFoundException("Session not found"));

        if (!session.getHostId().equals(userId)) {
            throw new AccessDeniedException("Only host can reveal answers");
        }

        // 2. Find Correct Option for Current Question
        // (Remember: index is 1-based in DB/UI, but 0-based in List, and we already
        // incremented it!)
        // So currentQuestionIndex is pointing to the NEXT question. We need the
        // PREVIOUS one (the active one).
        int activeIndex = session.getCurrentQuestionIndex() - 1;
        if (activeIndex < 0)
            throw new ApiException("No active question to reveal", HttpStatus.BAD_REQUEST);

        Question currentQuestion = session.getQuiz().getQuestions().get(activeIndex);

        Long correctOptionId = currentQuestion.getOptions().stream()
                .filter(Option::isCorrect)
                .findFirst()
                .map(Option::getId)
                .orElseThrow(() -> new IllegalStateException("Question has no correct answer!"));

        // 3. Generate Leaderboard (Top 5)
        List<LeaderboardEntryDto> leaderboard = playerRepository.findTop5ByGameSessionIdOrderByScoreDesc(sessionId)
                .stream()
                .map(p -> new LeaderboardEntryDto(p.getNickname(), p.getScore()))
                .toList();

        // 4. Broadcast Event
        RevealAnswerDto payload = new RevealAnswerDto(correctOptionId, leaderboard);
        messagingTemplate.convertAndSend("/topic/session/" + sessionId + "/players", payload);
    }

    // Optional: Standard GET endpoint if frontend wants to poll manually
    public List<LeaderboardEntryDto> getLeaderboard(String sessionId) {
        return playerRepository.findTop5ByGameSessionIdOrderByScoreDesc(sessionId)
                .stream()
                .map(p -> new LeaderboardEntryDto(p.getNickname(), p.getScore()))
                .toList();
    }

    private String generateUniquePin() {
        Random random = new Random();
        String pin;
        do {
            // Generate number between 100000 and 999999
            int number = 100000 + random.nextInt(900000);
            pin = String.valueOf(number);
        } while (sessionRepository.existsByGamePinAndStatusNot(pin, SessionStatus.FINISHED));
        return pin;
    }

    private void broadcastEvent(String sessionId, String eventType) {
        String destination = "/topic/session/" + sessionId + "/players";

        SessionEventDto event = new SessionEventDto(eventType, sessionId);

        System.out.println(">>> BROADCASTING " + eventType + " to " + destination);
        messagingTemplate.convertAndSend(destination, event);
    }
}
