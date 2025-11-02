# tests/test_full_conversion.py

import pytest
from src.agents.orchestrator import create_conversion_workflow

@pytest.mark.integration
def test_complete_conversion():
    """Test end-to-end conversion"""
    
    workflow = create_conversion_workflow()
    
    initial_state = ConversionState(
        github_url="https://github.com/janjakovacevic/SakilaProject",
        gemini_api_token=os.getenv("GEMINI_API_TOKEN"),
        target_framework="express",
        orm_choice="sequelize",
        repo_path=None,
        file_map=None,
        metadata=None,
        converted_components={},
        output_path=None,
        validation_result=None,
        errors=[]
    )
    
    # Execute workflow
    result = workflow.invoke(initial_state)
    
    # Assertions
    assert result["status"] == "completed"
    assert result["validation_result"]["valid"] == True
    assert os.path.exists(result["output_path"])
    assert os.path.exists(os.path.join(result["output_path"], "package.json"))
    assert os.path.exists(os.path.join(result["output_path"], "src/server.js"))
```

---

## 📊 Example End-to-End Flow

### Input: Simple Spring Boot Project
```
spring-customer-api/
├── pom.xml
└── src/main/java/com/example/
    ├── CustomerApiApplication.java
    ├── controller/
    │   └── CustomerController.java
    ├── service/
    │   └── CustomerService.java
    ├── repository/
    │   └── CustomerRepository.java
    └── entity/
        └── Customer.java