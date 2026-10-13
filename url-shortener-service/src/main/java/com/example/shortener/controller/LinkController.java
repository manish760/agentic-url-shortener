package com.example.shortener.controller;
import com.example.shortener.dto.*;
import com.example.shortener.service.LinkService;
import jakarta.validation.Valid;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.net.URI;
@RestController public class LinkController {
 private final LinkService service;
 public LinkController(LinkService service){this.service=service;}
 @PostMapping("/api/urls") public ResponseEntity<LinkResponse> create(@Valid @RequestBody CreateLinkRequest request){return ResponseEntity.status(HttpStatus.CREATED).body(service.create(request));}
 @GetMapping("/api/urls/{code}") public LinkResponse details(@PathVariable String code){return service.get(code);}
 @GetMapping("/api/urls/{code}/analytics") public LinkResponse analytics(@PathVariable String code){return service.get(code);}
 @DeleteMapping("/api/urls/{code}") @ResponseStatus(HttpStatus.NO_CONTENT) public void delete(@PathVariable String code){service.deactivate(code);}
 @GetMapping("/{code:[a-zA-Z0-9]{8}}") public ResponseEntity<Void> redirect(@PathVariable String code){return ResponseEntity.status(HttpStatus.FOUND).location(URI.create(service.resolve(code))).build();}
}
