package com.example.quizmaster.service;

import com.example.quizmaster.dto.QuizDto;
import com.example.quizmaster.dto.QuizSummaryDto;
import com.example.quizmaster.entity.Option;
import com.example.quizmaster.entity.Question;
import com.example.quizmaster.entity.Quiz;
import com.example.quizmaster.entity.User;
import com.example.quizmaster.repository.QuizRepository;
import com.example.quizmaster.repository.UserRepository;

import org.springframework.transaction.annotation.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.security.access.AccessDeniedException;

@Service
@Transactional
public class QuizService {

    @Autowired
    private QuizRepository quizRepository;

    @Autowired
    private UserRepository userRepository;

    public Quiz createQuiz(QuizDto.CreateRequest request, String userId) {
        // 1. Fetch the Creator (User)
        // We use the ID from Keycloak (JWT) to find our local User entity
        User creator = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found. Ensure sync is working."));

        // 2. Map Quiz Basic Info
        Quiz quiz = new Quiz();
        quiz.setTitle(request.getTitle());
        quiz.setDescription(request.getDescription());
        quiz.setPublic(request.isPublic());
        quiz.setCreator(creator); // Link the creator

        // 3. Map Questions (and maintain Order)
        if (request.getQuestions() != null) {
            int questionOrder = 0;

            for (QuizDto.QuestionRequest qDto : request.getQuestions()) {
                Question question = new Question();
                question.setText(qDto.getText());
                question.setPoints(qDto.getPoints());
                question.setType(qDto.getType());
                question.setTimeLimitSeconds(qDto.getTimeLimitSeconds());
                question.setOrderIndex(questionOrder++); // Auto-increment order

                // IMPORTANT: Link Parent to Child
                quiz.addQuestion(question);

                // 4. Map Options
                if (qDto.getOptions() != null) {
                    int optionOrder = 0;
                    for (QuizDto.OptionRequest oDto : qDto.getOptions()) {
                        Option option = new Option();
                        option.setText(oDto.getText());
                        option.setCorrect(oDto.isCorrect());
                        option.setOrderIndex(optionOrder++);

                        // IMPORTANT: Link Parent to Child
                        question.addOption(option);
                    }
                }
            }
        }

        // 5. Save Everything
        // Because of CascadeType.ALL, this saves Quiz, Questions, and Options
        return quizRepository.save(quiz);
    }

    public Page<QuizSummaryDto> getPublicQuizzes(int page, int size) {
        // 1. Create a PageRequest (Page 0 = First Page)
        // We sort by 'createdAt' descending so new quizzes show up first
        Pageable pageable = PageRequest.of(page, size, Sort.by("createdAt").descending());

        // 2. Fetch from DB
        Page<Quiz> quizPage = quizRepository.findByIsPublicTrue(pageable);

        // 3. Convert Entity -> DTO
        return quizPage.map(quiz -> new QuizSummaryDto(
                quiz.getId(),
                quiz.getTitle(),
                quiz.getDescription(),
                quiz.getCreator().getFirstName() + " " + quiz.getCreator().getLastName(),
                quiz.getCreatedAt(),
                quiz.getQuestions().size() // This might trigger a lazy load query
        ));
    }

    public void deleteQuiz(String quizId, String currentUserId) {
        // 1. Fetch the Quiz
        Quiz quiz = quizRepository.findById(quizId)
                .orElseThrow(() -> new RuntimeException("Quiz not found"));

        // 2. Validate Ownership
        // We compare the ID of the logged-in user with the ID of the creator
        if (!quiz.getCreator().getId().equals(currentUserId)) {
            throw new AccessDeniedException("You are not authorized to delete this quiz");
        }

        // 3. Delete
        // Because of CascadeType.ALL on the 'questions' list, this will
        // automatically delete all associated Questions and Options.
        quizRepository.delete(quiz);
    }
}
