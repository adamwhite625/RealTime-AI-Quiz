package com.example.quizmaster.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import com.example.quizmaster.entity.Option;

public interface OptionRepository extends JpaRepository<Option, Long> {
    // Custom methods if needed
}
