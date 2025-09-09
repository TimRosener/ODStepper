# Database Consultation Guide for All Agents

## 🚨 MANDATORY: When You MUST Consult the Database Architect Agent

### **Always Consult Database Architect Before:**

1. **Creating any new database tables**
2. **Modifying existing database schema** 
3. **Adding new types of analysis or data storage**
4. **Writing complex database queries**
5. **Storing user preferences or settings**
6. **Working with OLIS data import/export**
7. **Implementing multi-tenant features**

### **How to Consult the Database Architect:**

```
Hey @database-architect, I need to [describe your database need].

Current approach I'm considering: [your planned approach]

Please advise on the correct database pattern to use.
```

### **Example Consultation:**

```
Hey @database-architect, I need to store sentiment analysis results for public testimony.

Current approach I'm considering: Creating a new table called `testimony_sentiment_analysis` with columns for each emotion type.

Please advise on the correct database pattern to use.
```

**Database Architect Response:**
```
❌ REJECTED: Don't create new tables for analysis types. 

✅ CORRECT APPROACH: Use the extensible analysis framework:

1. Insert analysis type:
INSERT INTO analysis_types (type_code, type_name) 
VALUES ('testimony_sentiment', 'Testimony Sentiment Analysis');

2. Store results in measure_analyses:
INSERT INTO measure_analyses (measure_id, structured_data)
VALUES ('measure-id', '{"sentiment": 0.75, "emotions": {"joy": 0.8}}'::jsonb);

This keeps our architecture extensible and follows established patterns.
```

## **Quick Reference: What NOT to Do**

❌ **DON'T**: Create new tables for each type of analysis  
❌ **DON'T**: Modify OLIS import tables (measures, testimonies, etc.)  
❌ **DON'T**: Use rigid column structures for flexible data  
❌ **DON'T**: Write queries without company-level filtering  
❌ **DON'T**: Use integer IDs for new tables (use UUIDs)

## **Quick Reference: What TO Do**

✅ **DO**: Use the analysis_types + measure_analyses pattern  
✅ **DO**: Store flexible data in JSONB fields  
✅ **DO**: Follow existing multi-tenant security patterns  
✅ **DO**: Use UUID primary keys  
✅ **DO**: Consult Database Architect when in doubt

## **Emergency Contact**

If the Database Architect Agent is not available and you have an urgent database need:

1. **STOP** - Don't implement anything that could break architecture
2. **DOCUMENT** your need in detail
3. **WAIT** for Database Architect review
4. **NEVER** create new tables or modify schema without approval

**Remember: It's better to wait for proper guidance than to create technical debt that will cause problems later.**