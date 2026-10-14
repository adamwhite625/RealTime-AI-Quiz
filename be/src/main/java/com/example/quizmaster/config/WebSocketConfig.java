package com.example.quizmaster.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        // 1. The HTTP URL clients connect to initially (e.g. ws://localhost:8080/ws)
        registry.addEndpoint("/ws")
                .setAllowedOriginPatterns("*") // Allow all origins for development (CORS)
                .withSockJS(); // Enable SockJS fallback options
    }

    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        // 2. Prefixes for messages FROM client TO server (not used much here yet)
        registry.setApplicationDestinationPrefixes("/app");

        // 3. Prefixes for messages FROM server TO client
        // Clients will subscribe to /topic/session/{id}
        registry.enableSimpleBroker("/topic");
    }
}
