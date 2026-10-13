package com.example.shortener;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
@SpringBootTest @AutoConfigureMockMvc class LinkControllerTest {
 @Autowired MockMvc mvc;
 @Test void createAndRejectInvalidUrl() throws Exception {
  mvc.perform(post("/api/urls").contentType(MediaType.APPLICATION_JSON).content("{\"url\":\"https://example.com/path\"}"))
    .andExpect(status().isCreated()).andExpect(jsonPath("$.code").isNotEmpty());
  mvc.perform(post("/api/urls").contentType(MediaType.APPLICATION_JSON).content("{\"url\":\"file:///etc/passwd\"}"))
    .andExpect(status().isBadRequest());
 }
}
