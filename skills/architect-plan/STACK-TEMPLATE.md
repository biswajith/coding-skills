# STACK.md — Project Tech Stack

> Copy this file to `.claude/STACK.md` in your project root and fill it in.
> Read by ALL skills: architect-plan, tdd-workflow, code-review, plan-adherence,
> github-review-comments, mysql-debug, solr-debug, and jellyfish-insights.
> Delete sections that don't apply to your stack.

## Project Overview
- **Name:**
- **Purpose:** (1-2 sentences)

## Core Stack
- **Java version:** (e.g., Java 21)
- **Spring Boot version:**
- **Build tool:** (Maven / Gradle)
- **Database:** (e.g., MySQL 8, PostgreSQL 15)
- **ORM:** (e.g., Hibernate 6, Spring Data JPA)
- **Migration tool:** (e.g., Liquibase / Flyway)

## Search
- **Solr version:**
- **Solr client:** (e.g., Spring Data Solr, SolrJ direct)
- **Core/collection names:**

## AI / Agentic
- **OpenAI SDK:** (e.g., openai-java, Spring AI)
- **Models in use:** (e.g., gpt-4o, gpt-4o-mini)
- **Google ADK version:** (if applicable)
- **Agent tools defined:** (list)

## API Layer
- **Style:** (REST / GraphQL / both)
- **Auth mechanism:** (e.g., JWT, Spring Security OAuth2)
- **API versioning strategy:** (e.g., /api/v1/)

## Testing
- **Unit test framework:** (e.g., JUnit 5 + Mockito)
- **Integration test framework:** (e.g., Spring Boot Test, Testcontainers)
- **Coverage target:** (e.g., 80% line coverage)
- **Test naming convention:** (e.g., should_doX_when_Y)

## Conventions
- **Package structure:** (e.g., com.example.app.{domain}.{layer})
- **DTO pattern:** (e.g., Java records, Lombok @Data)
- **Error handling:** (e.g., @ControllerAdvice with ProblemDetail)
- **Logging:** (e.g., SLF4J + Logback, structured JSON logs)

## Infrastructure
- **Deployment target:** (e.g., Docker + Kubernetes, AWS ECS)
- **Config management:** (e.g., Spring Cloud Config, env vars)

## Database Connection (used by mysql-debug skill)
- **DB_HOST:** (e.g., localhost)
- **DB_PORT:** (e.g., 3306)
- **DB_NAME:** (your database name)
- **DB_USER:** (your database user)
- **DB_PASSWORD:** (leave blank — set via env var, do not commit passwords)

## Solr Connection (used by solr-debug skill)
- **SOLR_URL:** (e.g., http://localhost:8983/solr)

## Known Constraints / Gotchas
- (List anything the architect and reviewers should be aware of)
