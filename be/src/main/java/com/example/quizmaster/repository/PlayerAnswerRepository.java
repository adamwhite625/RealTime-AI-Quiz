package com.example.quizmaster.repository;

import com.example.quizmaster.entity.Player;
import com.example.quizmaster.entity.PlayerAnswer;
import com.example.quizmaster.entity.Question;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface PlayerAnswerRepository extends JpaRepository<PlayerAnswer, Long> {

    // Check if this specific player has already answered this specific question
    boolean existsByPlayerAndQuestion(Player player, Question question);

    // Count how many answers have been submitted for this question (for Host UI)
    @Query("SELECT COUNT(pa) FROM PlayerAnswer pa " +
            "WHERE pa.question = :question " +
            "AND pa.player.gameSession.id = :sessionId")
    int countByQuestionAndSession(@Param("question") Question question,
            @Param("sessionId") String sessionId);
}