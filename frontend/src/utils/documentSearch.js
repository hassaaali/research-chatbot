export class DocumentSearch {
  constructor(pdfProcessor) {
    this.pdfProcessor = pdfProcessor;
  }

  async processQuery(query, documentIds = null) {
    const searchResults = this.pdfProcessor.searchInDocuments(query, documentIds);
    
    if (searchResults.length === 0) {
      return {
        response: "I couldn't find any relevant information about your query in the uploaded documents. Could you try rephrasing your question or check if the documents contain the information you're looking for?",
        citations: [],
        sources: []
      };
    }

    return this.generateResponse(query, searchResults);
  }

  generateResponse(query, searchResults) {
    const response = this.createContextualResponse(query, searchResults);
    const citations = this.extractCitations(searchResults);
    const sources = this.extractSources(searchResults);

    return {
      response,
      citations,
      sources
    };
  }

  createContextualResponse(query, searchResults) {
    const queryLower = query.toLowerCase();
    let response = "";

    // Determine the type of query
    const isDefinition = this.isDefinitionQuery(queryLower);
    const isComparison = this.isComparisonQuery(queryLower);
    const isSummary = this.isSummaryQuery(queryLower);
    const isMethodology = this.isMethodologyQuery(queryLower);

    if (isDefinition) {
      response += this.generateDefinitionResponse(searchResults);
    } else if (isComparison) {
      response += this.generateComparisonResponse(searchResults);
    } else if (isSummary) {
      response += this.generateSummaryResponse(searchResults);
    } else if (isMethodology) {
      response += this.generateMethodologyResponse(searchResults);
    } else {
      response += this.generateGeneralResponse(searchResults);
    }

    return response;
  }

  isDefinitionQuery(query) {
    const definitionKeywords = [
      'what is', 'define', 'definition', 'meaning', 'explain',
      'what are', 'what does', 'how is', 'describe'
    ];
    return definitionKeywords.some(keyword => query.includes(keyword));
  }

  isComparisonQuery(query) {
    const comparisonKeywords = [
      'compare', 'comparison', 'difference', 'versus', 'vs',
      'similar', 'different', 'contrast', 'between'
    ];
    return comparisonKeywords.some(keyword => query.includes(keyword));
  }

  isSummaryQuery(query) {
    const summaryKeywords = [
      'summarize', 'summary', 'overview', 'main points',
      'key findings', 'conclusions', 'results'
    ];
    return summaryKeywords.some(keyword => query.includes(keyword));
  }

  isMethodologyQuery(query) {
    const methodologyKeywords = [
      'methodology', 'method', 'approach', 'procedure',
      'how', 'process', 'steps', 'technique'
    ];
    return methodologyKeywords.some(keyword => query.includes(keyword));
  }

  generateDefinitionResponse(searchResults) {
    const topMatches = searchResults
      .flatMap(result => result.matches)
      .sort((a, b) => b.score - a.score)
      .slice(0, 3);

    let response = "Based on the research papers, here's what I found:\n\n";
    
    topMatches.forEach((match, index) => {
      const docName = searchResults.find(r => r.matches.includes(match))?.document.name || 'Unknown';
      response += `${match.context} [${index + 1}]\n\n`;
    });

    return response;
  }

  generateComparisonResponse(searchResults) {
    let response = "Here's a comparison based on the research papers:\n\n";
    
    searchResults.forEach((result, index) => {
      const topMatch = result.matches[0];
      response += `**From "${result.document.name}":**\n`;
      response += `${topMatch.context} [${index + 1}]\n\n`;
    });

    return response;
  }

  generateSummaryResponse(searchResults) {
    let response = "Here's a summary of the key findings:\n\n";
    
    const topMatches = searchResults
      .flatMap(result => result.matches.slice(0, 2))
      .sort((a, b) => b.score - a.score);

    topMatches.forEach((match, index) => {
      const docName = searchResults.find(r => r.matches.includes(match))?.document.name || 'Unknown';
      response += `• ${match.text.replace(/^\W+/, '')} [${index + 1}]\n\n`;
    });

    return response;
  }

  generateMethodologyResponse(searchResults) {
    let response = "Here are the methodologies and approaches mentioned:\n\n";
    
    searchResults.forEach((result, index) => {
      const relevantMatches = result.matches.filter(match => 
        match.text.toLowerCase().includes('method') ||
        match.text.toLowerCase().includes('approach') ||
        match.text.toLowerCase().includes('procedure')
      );

      if (relevantMatches.length > 0) {
        response += `**From "${result.document.name}":**\n`;
        response += `${relevantMatches[0].context} [${index + 1}]\n\n`;
      }
    });

    return response;
  }

  generateGeneralResponse(searchResults) {
    let response = "Based on your research papers, here's what I found:\n\n";
    
    const topMatches = searchResults
      .flatMap(result => result.matches)
      .sort((a, b) => b.score - a.score)
      .slice(0, 4);

    topMatches.forEach((match, index) => {
      const docName = searchResults.find(r => r.matches.includes(match))?.document.name || 'Unknown';
      response += `${match.context} [${index + 1}]\n\n`;
    });

    return response;
  }

  extractCitations(searchResults) {
    const citations = [];
    let citationIndex = 1;

    searchResults.forEach(result => {
      result.matches.slice(0, 2).forEach(match => {
        citations.push({
          id: citationIndex,
          document: result.document.name,
          text: match.text,
          context: match.context,
          score: match.score
        });
        citationIndex++;
      });
    });

    return citations.sort((a, b) => b.score - a.score);
  }

  extractSources(searchResults) {
    return searchResults.map(result => ({
      name: result.document.name,
      pages: result.document.pages,
      relevantMatches: result.matches.length
    }));
  }

  // Enhanced query processing for better results
  preprocessQuery(query) {
    // Remove common stop words that don't add value
    const stopWords = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'];
    const words = query.toLowerCase().split(/\s+/);
    const filteredWords = words.filter(word => !stopWords.includes(word) && word.length > 2);
    
    return filteredWords.join(' ');
  }

  // Suggest related queries based on document content
  suggestRelatedQueries(documentIds = null) {
    const docs = documentIds 
      ? documentIds.map(id => this.pdfProcessor.getDocument(id)).filter(Boolean)
      : this.pdfProcessor.getAllDocuments();

    const suggestions = [
      "What are the main findings?",
      "Summarize the methodology",
      "What are the key conclusions?",
      "Compare the different approaches",
      "What are the limitations mentioned?"
    ];

    return suggestions;
  }
}

export default DocumentSearch;