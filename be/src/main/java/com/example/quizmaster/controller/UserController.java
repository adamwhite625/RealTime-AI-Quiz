package com.example.quizmaster.controller;

import com.example.quizmaster.dto.AuthDto;
import com.example.quizmaster.service.UserService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/me")
    // Update the ResponseEntity type
    public ResponseEntity<com.example.quizmaster.dto.UserProfileDto> getCurrentUser(@AuthenticationPrincipal Jwt jwt) {
        String userId = jwt.getSubject();
        return ResponseEntity.ok(userService.getUserById(userId));
    }

    @PostMapping("/auth/signin")
    public ResponseEntity<AuthDto.LoginResponse> signin(@RequestBody AuthDto.LoginRequest loginRequest) {
        return ResponseEntity.status(HttpStatus.OK).body(userService.login(loginRequest));
    }

    @PostMapping("/auth/signup")
    public ResponseEntity<AuthDto.MessageResponse> signup(
            @RequestBody AuthDto.SignUpRequest signUpRequest) {
        return ResponseEntity.status(HttpStatus.CREATED).body(userService.register(signUpRequest));
    }
}
