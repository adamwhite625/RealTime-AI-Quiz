package com.example.quizmaster.repository;

import com.example.quizmaster.entity.Quiz;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface QuizRepository extends JpaRepository<Quiz, String> {

    // Finds all public quizzes and returns a "Page" object containing metadata
    // (total pages, etc.)
    Page<Quiz> findByIsPublicTrue(Pageable pageable);
}