package com.example.shortener.dto;
import jakarta.validation.constraints.NotBlank;
import java.time.Instant;
public record CreateLinkRequest(@NotBlank String url,Instant expiresAt){}
