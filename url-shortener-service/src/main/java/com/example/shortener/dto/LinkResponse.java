package com.example.shortener.dto;
import java.time.Instant;
public record LinkResponse(String code,String shortUrl,String originalUrl,Instant createdAt,Instant expiresAt,long totalClicks,boolean active){}
