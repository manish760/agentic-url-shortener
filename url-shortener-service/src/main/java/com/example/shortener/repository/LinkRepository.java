package com.example.shortener.repository;
import com.example.shortener.entity.ShortLink;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
public interface LinkRepository extends JpaRepository<ShortLink,Long>{Optional<ShortLink> findByCode(String code);}
