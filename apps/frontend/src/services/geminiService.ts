
import { GoogleGenAI, Type } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

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
