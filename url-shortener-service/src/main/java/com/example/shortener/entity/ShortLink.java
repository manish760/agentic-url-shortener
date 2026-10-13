package com.example.shortener.entity;
import jakarta.persistence.*;
import java.time.Instant;
@Entity @Table(name="short_links",indexes=@Index(name="idx_short_code",columnList="code",unique=true))
public class ShortLink {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) public Long id;
 @Column(nullable=false,unique=true,length=16) public String code;
 @Column(nullable=false,length=2048) public String originalUrl;
 @Column(nullable=false) public Instant createdAt=Instant.now();
 public Instant expiresAt;
 @Column(nullable=false) public long clicks=0;
 @Column(nullable=false) public boolean active=true;
 protected ShortLink(){}
 public ShortLink(String code,String originalUrl,Instant expiresAt){this.code=code;this.originalUrl=originalUrl;this.expiresAt=expiresAt;}
}
