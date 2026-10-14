package com.example.quizmaster.dto;

import java.time.LocalDateTime;

public class QuizSummaryDto {
    private String id;
    private String title;
    private String description;
    private String creatorName; // Helpful to show "Created by John"
    private LocalDateTime createdAt;
    private int questionCount; // Helpful for users to know length

    // Constructor
    public QuizSummaryDto(String id, String title, String description,
            String creatorName,
            LocalDateTime createdAt, int questionCount) {
        this.id = id;
        this.title = title;
        this.description = description;
        this.creatorName = creatorName;
        this.createdAt = createdAt;
        this.questionCount = questionCount;
    }

    // Getters and Setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getCreatorName() {
        return creatorName;
    }

    public void setCreatorName(String creatorName) {
        this.creatorName = creatorName;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public int getQuestionCount() {
        return questionCount;
    }

    public void setQuestionCount(int questionCount) {
        this.questionCount = questionCount;
    }
}