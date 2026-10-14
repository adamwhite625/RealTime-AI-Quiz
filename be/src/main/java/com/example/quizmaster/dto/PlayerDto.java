package com.example.quizmaster.dto;

public class PlayerDto {
    public static class PlayerJoinedMessage {
        public String type = "PLAYER_JOINED";
        public String nickname;
        public Long playerId;

        public PlayerJoinedMessage(String nickname, Long playerId) {
            this.nickname = nickname;
            this.playerId = playerId;
        }
    }

    public static class PlayerLeftMessage {
        public String type = "PLAYER_LEFT";
        public String nickname;
        public Long playerId;

        public PlayerLeftMessage(String nickname, Long playerId) {
            this.nickname = nickname;
            this.playerId = playerId;
        }
    }
}
