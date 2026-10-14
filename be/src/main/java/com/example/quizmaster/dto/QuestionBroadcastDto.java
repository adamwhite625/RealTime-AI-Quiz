package com.example.quizmaster.dto;

import java.util.List;

public class QuestionBroadcastDto {
    private String type; // "NEXT_QUESTION"
    private Long questionId;
    private String text;
    private Integer timeLimitSeconds;
    private Integer currentQuestionNumber; // e.g., 1
    private Integer totalQuestions; // e.g., 10
    private List<OptionDto> options;

    // Constructor
    public QuestionBroadcastDto(String type, Long questionId, String text, Integer timeLimit,
            int current, int total, List<OptionDto> options) {
        this.type = type;
        this.questionId = questionId;
        this.text = text;
        this.timeLimitSeconds = timeLimit;
        this.currentQuestionNumber = current;
        this.totalQuestions = total;
        this.options = options;
    }

    // Inner DTO for Options (No 'isCorrect' field!)
    public static class OptionDto {
        private Long id;
        private String text;
        private Integer orderIndex;

        public OptionDto(Long id, String text, Integer orderIndex) {
            this.id = id;
            this.text = text;
            this.orderIndex = orderIndex;
        }

        // Getters and Setters
        public Long getId() {
            return id;
        }

        public void setId(Long id) {
            this.id = id;
        }

        public String getText() {
            return text;
        }

        public void setText(String text) {
            this.text = text;
        }

        public Integer getOrderIndex() {
            return orderIndex;
        }

        public void setOrderIndex(Integer orderIndex) {
            this.orderIndex = orderIndex;
        }
    }

    // Getters and Setters
    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public Long getQuestionId() {
        return questionId;
    }

    public void setQuestionId(Long questionId) {
        this.questionId = questionId;
    }

    public String getText() {
        return text;
    }

    public void setText(String text) {
        this.text = text;
    }

    public Integer getTimeLimitSeconds() {
        return timeLimitSeconds;
    }

    public void setTimeLimitSeconds(Integer timeLimitSeconds) {
        this.timeLimitSeconds = timeLimitSeconds;
    }

    public Integer getCurrentQuestionNumber() {
        return currentQuestionNumber;
    }

    public void setCurrentQuestionNumber(Integer currentQuestionNumber) {
        this.currentQuestionNumber = currentQuestionNumber;
    }

    public Integer getTotalQuestions() {
        return totalQuestions;
    }

    public void setTotalQuestions(Integer totalQuestions) {
        this.totalQuestions = totalQuestions;
    }

    public List<OptionDto> getOptions() {
        return options;
    }

    public void setOptions(List<OptionDto> options) {
        this.options = options;
    }
}
