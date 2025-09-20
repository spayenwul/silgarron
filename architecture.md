```mermaid
graph TD
    main --> game
    game --> director
    director --> intent_service
    director --> llm_service
```