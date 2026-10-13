package com.example.shortener.service;
import com.example.shortener.dto.*;
import com.example.shortener.entity.ShortLink;
import com.example.shortener.repository.LinkRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import java.net.URI;
import java.security.SecureRandom;
import java.time.Instant;
@Service public class LinkService {
 private static final String ALPHABET="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
 private final SecureRandom random=new SecureRandom();
 private final LinkRepository repo;
 private final String baseUrl;
 public LinkService(LinkRepository repo,@Value("${app.base-url:http://localhost:8080}") String baseUrl){this.repo=repo;this.baseUrl=baseUrl;}
 @Transactional public LinkResponse create(CreateLinkRequest request){
  validateUrl(request.url());
  if(request.expiresAt()!=null && !request.expiresAt().isAfter(Instant.now())) throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Expiry must be in future");
  for(int attempt=0;attempt<10;attempt++){
   String code=newCode(); if(repo.findByCode(code).isPresent())continue;
   return map(repo.saveAndFlush(new ShortLink(code,request.url(),request.expiresAt())));
  }
  throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Could not allocate short code");
 }
 private void validateUrl(String url){
  try {URI uri=URI.create(url);String scheme=uri.getScheme();
   if(scheme==null || !(scheme.equalsIgnoreCase("http")||scheme.equalsIgnoreCase("https")) || uri.getHost()==null || url.length()>2048 || uri.getUserInfo()!=null)
    throw new IllegalArgumentException();
  } catch(Exception ex){throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Valid HTTP(S) URL required");}
 }
 private String newCode(){StringBuilder b=new StringBuilder();for(int i=0;i<8;i++)b.append(ALPHABET.charAt(random.nextInt(ALPHABET.length())));return b.toString();}
 @Transactional public String resolve(String code){
  ShortLink link=find(code);
  if(!link.active || (link.expiresAt!=null && !link.expiresAt.isAfter(Instant.now())))throw new ResponseStatusException(HttpStatus.GONE,"Link unavailable");
  link.clicks++;return link.originalUrl;
 }
 @Transactional(readOnly=true) public LinkResponse get(String code){return map(find(code));}
 @Transactional public void deactivate(String code){find(code).active=false;}
 private ShortLink find(String code){return repo.findByCode(code).orElseThrow(()->new ResponseStatusException(HttpStatus.NOT_FOUND,"Link not found"));}
 private LinkResponse map(ShortLink link){return new LinkResponse(link.code,baseUrl+"/"+link.code,link.originalUrl,link.createdAt,link.expiresAt,link.clicks,link.active);}
}
