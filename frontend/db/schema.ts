import { pgTable, serial, text, jsonb, timestamp, boolean, uuid, varchar } from "drizzle-orm/pg-core";
import z from "zod";

export const chats = pgTable("chats", {
  id: serial("id").primaryKey(),
  user_id: text("user_id").notNull(),
  query: text("query").notNull(),
  response: text("response").notNull(),
  created_at: timestamp("created_at").defaultNow(),
});

export const chat_memory = pgTable("chat_memory", {
  id: serial("id").primaryKey(),
  user_id: text("user_id").notNull(),
  memory: jsonb("memory").default([]),
  updated_at: timestamp("updated_at").defaultNow(),
});

export const reports = pgTable("reports", {
  id: serial("id").primaryKey(),
  idea: text("idea").notNull(),
  result_json: jsonb("result_json").notNull(),
  report_md: text("report_md").notNull(),
  created_at: timestamp("created_at").defaultNow(),
});


export const signUpFormSchema = z.object({
  name: z.string().min(1, {message: "Nmae is required."}),
  email: z.string().email(),
  password: z.string().min(1, {message: "Password is required"}),
  confirmPassword: z.string().min(1, {message: "Password is required"})
}).refine((data) => data.password === data.confirmPassword, {
  message: "Paswords do not match",
  path: ["confirmPassword"]
})

export const signInFormSchema = z.object({
    email: z.string().email(),
    password: z.string().min(1, { message: 'Password is required' })
})

export const user = pgTable("user", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  email: text("email").notNull().unique(),
  emailVerified: boolean("email_verified").default(false).notNull(),
  image: text("image"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().$onUpdate(() => new Date()).notNull(),
});

export const session = pgTable("session", {
  id: text("id").primaryKey(),
  expiresAt: timestamp("expires_at").notNull(),
  token: text("token").notNull().unique(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").$onUpdate(() => new Date()).notNull(),
  ipAddress: text("ip_address"),
  userAgent: text("user_agent"),
  userId: text("user_id").notNull().references(() => user.id, { onDelete: "cascade" }),
});

export const account = pgTable("account", {
  id: text("id").primaryKey(),
  accountId: text("account_id").notNull(),
  providerId: text("provider_id").notNull(),
  userId: text("user_id").notNull().references(() => user.id, { onDelete: "cascade" }),
  accessToken: text("access_token"),
  refreshToken: text("refresh_token"),
  idToken: text("id_token"),
  accessTokenExpiresAt: timestamp("access_token_expires_at"),
  refreshTokenExpiresAt: timestamp("refresh_token_expires_at"),
  scope: text("scope"),
  password: text("password"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").$onUpdate(() => new Date()).notNull(),
});

export const verification = pgTable("verification", {
  id: text("id").primaryKey(),
  identifier: text("identifier").notNull(),
  value: text("value").notNull(),
  expiresAt: timestamp("expires_at").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().$onUpdate(() => new Date()).notNull(),
});

export const researchReport = pgTable("research_report", {
    id: uuid("id").defaultRandom().primaryKey(),
    idea: text("idea").notNull(),
    marketAnalysis: text("market_analysis").notNull(),
    competitorAnalysis: text("competitor_analysis").notNull(),
    keyInsights: text("key_insights").notNull(),
    generatedAt: timestamp("generated_at").defaultNow().notNull(),
    userId: text("user_id").notNull().references(() => user.id, { onDelete: "cascade" }),
});