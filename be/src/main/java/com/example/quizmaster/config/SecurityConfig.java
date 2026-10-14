package com.example.quizmaster.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .csrf(AbstractHttpConfigurer::disable)
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/", "/index.html", "/host.html", "/player.html", "/tester.html").permitAll()
                        .requestMatchers("/css/**", "/js/**", "/images/**").permitAll()
                        .requestMatchers(HttpMethod.POST, "/api/users/auth/**").permitAll()
                        .requestMatchers(HttpMethod.POST, "/api/sessions/join").permitAll()
                        .requestMatchers(HttpMethod.POST, "/api/sessions/*/players").permitAll()
                        .requestMatchers(HttpMethod.POST, "/api/sessions/*/questions/*/answers").permitAll()
                        .requestMatchers(HttpMethod.POST, "/api/sessions/*/submit-answer").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/sessions/*/state").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/sessions/*/leaderboard").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/quizzes", "/api/quizzes/**").permitAll()
                        .requestMatchers("/ws/**").permitAll()
                        .requestMatchers("/v3/api-docs/**", "/swagger-ui/**", "/swagger-ui.html").permitAll()
                        .anyRequest().authenticated())
                .oauth2ResourceServer(oauth2 -> oauth2
                        .jwt(Customizer.withDefaults()));

        return http.build();
    }
}
