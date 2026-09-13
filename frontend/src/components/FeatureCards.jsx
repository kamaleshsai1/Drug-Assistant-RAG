function FeatureCards({ onFeatureSelect }) {
  const features = [
    {
      id: "web",
      title: "Web Search",
      description: "Search the web for current information",
    },
    {
      id: "pdf",
      title: "Ask a PDF",
      description: "Ask questions about uploaded documents",
    },
    {
      id: "ocr",
      title: "Image Analysis",
      description: "Analyze medicine or document images",
    },
  ];

  const handleClick = (featureId) => {
    if (typeof onFeatureSelect === "function") {
      onFeatureSelect(featureId);
    }
  };

  return (
    <div
      className="feature-cards"
      style={{
        width: "min(1050px, calc(100% - 40px))",
        margin: "28px auto 0",
        display: "grid",
        gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
        gap: "12px",
      }}
    >
      {features.map((feature) => {
        return (
          <button
            key={feature.id}
            type="button"
            onClick={() => handleClick(feature.id)}
            style={{
              border: "1px solid #e3e3e6",
              borderRadius: "14px",
              background: "#fff",
              padding: "22px 18px",
              minHeight: "125px",
              textAlign: "left",
              cursor: "pointer",
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-start",
              justifyContent: "center",
              gap: "10px",
              transition:
                "border-color 0.15s ease, transform 0.15s ease",
            }}
            onMouseEnter={(event) => {
              event.currentTarget.style.borderColor = "#c8c8cc";
              event.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseLeave={(event) => {
              event.currentTarget.style.borderColor = "#e3e3e6";
              event.currentTarget.style.transform = "translateY(0)";
            }}
          >
            <span
              style={{
                fontSize: "15px",
                fontWeight: 600,
                color: "#25272c",
              }}
            >
              {feature.title}
            </span>

            <span
              style={{
                fontSize: "12px",
                lineHeight: 1.5,
                color: "#858994",
              }}
            >
              {feature.description}
            </span>
          </button>
        );
      })}
    </div>
  );
}

export default FeatureCards;