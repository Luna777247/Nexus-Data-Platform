
import { GoogleGenAI, Type } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: import.meta.env.VITE_GEMINI_API_KEY || process.env.GEMINI_API_KEY });

export const generateHybridRecommendations = async () => {
  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: `Generate a JSON dataset of 15 premium travel recommendations for a Hybrid Recommender System. 
      Include: id, name, city, category, rating (4.0-5.0), reviewsCount, avgPrice (VND), tags (array), 
      matchScore (0.85-0.99), recommendationType ('Hybrid').
      Ensure destinations are diverse (Vietnam and International).`,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.ARRAY,
          items: {
            type: Type.OBJECT,
            properties: {
              id: { type: Type.STRING },
              name: { type: Type.STRING },
              city: { type: Type.STRING },
              category: { type: Type.STRING },
              rating: { type: Type.NUMBER },
              reviewsCount: { type: Type.INTEGER },
              avgPrice: { type: Type.NUMBER },
              tags: { type: Type.ARRAY, items: { type: Type.STRING } },
              matchScore: { type: Type.NUMBER },
              recommendationType: { type: Type.STRING }
            },
            required: ["id", "name", "city", "category", "rating", "reviewsCount", "avgPrice", "tags", "matchScore", "recommendationType"]
          }
        }
      }
    });
    return JSON.parse(response.text);
  } catch (error) {
    console.error("Hybrid Gen Error:", error);
    return [];
  }
};

export const chatWithAnalyst = async (history: any[], data: any[]) => {
  try {
    const chat = ai.chats.create({
      model: 'gemini-3-flash-preview',
      config: {
        systemInstruction: `You are Nexus AI Platform Architect. You help users manage their Data Platform (ETL, Lake, Warehouse, Hybrid Recommender). 
        You explain how the hybrid model combines Content-based filtering (tags) and Collaborative filtering (user ratings) to generate travel suggestions.
        Answer specifically about the technical architecture and data insights in Vietnamese.`
      }
    });
    const lastMessage = history[history.length - 1].parts[0].text;
    const response = await chat.sendMessage({ message: lastMessage });
    return response.text;
  } catch (error) {
    return "Lỗi hệ thống phân tích. Vui lòng thử lại.";
  }
};

export const generateSyntheticData = async (count: number = 20) => {
  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: `Generate ${count} processed travel fact records for a Data Warehouse. Include SQL transformation logs representing the cleaning phase.`,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.ARRAY,
          items: {
            type: Type.OBJECT,
            properties: {
              id: { type: Type.INTEGER },
              timestamp: { type: Type.STRING },
              region: { type: Type.STRING },
              category: { type: Type.STRING },
              metricValue: { type: Type.NUMBER },
              qualityScore: { type: Type.NUMBER },
              transformationLog: { type: Type.STRING }
            },
            required: ["id", "timestamp", "region", "category", "metricValue", "qualityScore", "transformationLog"]
          }
        }
      }
    });
    return JSON.parse(response.text);
  } catch (error) {
    return [];
  }
};

/**
 * Generate data source configuration using AI
 * User provides basic info, AI generates optimal config
 */
export const generateDataSourceConfig = async (basicInfo: {
  source_id: string;
  source_name: string;
  location: string;
  category: 'application' | 'database' | 'streaming' | 'external';
  source_type?: string;
}) => {
  try {
    const prompt = `You are a Data Engineering expert. Generate optimal configuration for a data source with these details:

Source ID: ${basicInfo.source_id}
Source Name: ${basicInfo.source_name}
Location/URL: ${basicInfo.location}
Category: ${basicInfo.category}
${basicInfo.source_type ? `Type: ${basicInfo.source_type}` : ''}

Based on the URL/location pattern and category, intelligently suggest:
1. kafka_topic: Kafka topic name (format: topic_<source_type>_<context>)
2. target_table: Target table name (format: bronze_<entity>)
3. schedule_interval: Cron or preset (@hourly, @daily, etc) based on data freshness needs
4. method: HTTP method if API (GET, POST, etc)
5. auth_type: Authentication type (bearer, api_key, oauth, none)
6. format: Data format (json, xml, csv, parquet)
7. required_fields: Array of critical fields that must exist (infer from source type)
8. description: Brief description of what this source provides
9. batch_size: Optimal batch size for extraction (100-5000)
10. retention_days: Data retention period (30-730 days)

Follow best practices for data engineering and ETL patterns.`;

    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            kafka_topic: { type: Type.STRING },
            target_table: { type: Type.STRING },
            schedule_interval: { type: Type.STRING },
            method: { type: Type.STRING },
            auth_type: { type: Type.STRING },
            format: { type: Type.STRING },
            required_fields: { 
              type: Type.ARRAY, 
              items: { type: Type.STRING } 
            },
            description: { type: Type.STRING },
            batch_size: { type: Type.INTEGER },
            retention_days: { type: Type.INTEGER }
          },
          required: [
            "kafka_topic", 
            "target_table", 
            "schedule_interval", 
            "format", 
            "description"
          ]
        }
      }
    });

    return JSON.parse(response.text);
  } catch (error) {
    console.error("AI Config Generation Error:", error);
    throw new Error("Failed to generate AI configuration");
  }
};
