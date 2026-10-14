package com.example.quizmaster.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "player_answers", uniqueConstraints = {
        @UniqueConstraint(columnNames = { "player_id", "question_id" }) // Prevent double answers
})
public class PlayerAnswer {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "player_id", nullable = false)
    private Player player;

    @ManyToOne
    @JoinColumn(name = "question_id", nullable = false)
    private Question question;

    @ManyToOne
    @JoinColumn(name = "selected_option_id", nullable = false)
    private Option selectedOption;

    private int scoreAwarded; // 0 if wrong, calc value if right

    private boolean isCorrect;

    // Constructors, Getters, Setters
    public PlayerAnswer() {
    }

    public PlayerAnswer(Player player, Question question, Option selectedOption, int scoreAwarded, boolean isCorrect) {
        this.player = player;
        this.question = question;
        this.selectedOption = selectedOption;
        this.scoreAwarded = scoreAwarded;
        this.isCorrect = isCorrect;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Player getPlayer() {
        return player;
    }

    public void setPlayer(Player player) {
        this.player = player;
    }

    public Question getQuestion() {
        return question;
    }

    public void setQuestion(Question question) {
        this.question = question;
    }

    public Option getSelectedOption() {
        return selectedOption;
    }

    public void setSelectedOption(Option selectedOption) {
        this.selectedOption = selectedOption;
    }

    public int getScoreAwarded() {
        return scoreAwarded;
    }

    public void setScoreAwarded(int scoreAwarded) {
        this.scoreAwarded = scoreAwarded;
    }

    public boolean isCorrect() {
        return isCorrect;
    }

    public void setCorrect(boolean isCorrect) {
        this.isCorrect = isCorrect;
    }
}