import axios from "axios";
import { NextResponse } from "next/server";

interface Article {
    title: string;
    source: {
        id: string | null;
        name: string;
    };
    url: string;
    publishedAt: string;
    description: string;
}

export async function trendScraper(idea: string) {

    try {
        const apiKey =  process.env.NEWS_API_KEY
        if (!apiKey) throw new Error("No API Key.")

        // what is encodeURIComponenet
        const query = encodeURIComponent(idea)
        const url = `http://newsapi.org/v2/everything?q=${query}&sortBy=publishedAt&pageSize=5&apiKey=${apiKey}`
        const response = await axios.get(url)

        const articles = response.data.articles.map((a: Article) => ({
            title: a.title,
            source: a.source,
            url: a.url,
            publishedAt: a.publishedAt,
            snippet: a.description        
        }))

        return {
            agent: "TrendScrapper",
            idea,
            trends: articles,
            fetchedAt: new Date()
        }

    } catch (error) {
        console.error("Error fetching trends.", error)
        return NextResponse.json({error: "TrendScrapper: Failed to fetch news."})
    }
}