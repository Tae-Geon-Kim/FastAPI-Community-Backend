```mermaid
%%{init: {"theme": "neutral", "cssStyles": ".er.relationshipLabelBox { fill: white !important; fill-opacity: 1 !important; stroke: none !important; } .er.relationshipLabel { fill: black !important; }"}}%%
erDiagram
    direction LR
	user {
		int index PK ""
		varchar id  ""  
		text password  ""  
		timestamp reg_date  ""  
		timestamp update_date  ""  
	}

	boards {
		int index PK ""  
		varchar title  ""  
		text content  ""  
		timestamp reg_date  ""  
		timestamp update_date  ""
		int user_index FK ""
	}

	user||--o{boards: "작성"
```