/**
 * Lightweight visual quality checker using GPT-4o-mini with vision
 * Detects AI artifacts, weirdness, and quality issues in generated images
 */

import OpenAI from 'openai';

export interface QualityCheckResult {
  passed: boolean;
  score: number; // 0-100
  issues: QualityIssue[];
  recommendation: 'approve' | 'regenerate' | 'manual_review';
  explanation: string;
}

export interface QualityIssue {
  type: 'artifact' | 'anatomy' | 'proportions' | 'text' | 'blur' | 'distortion' | 'other';
  severity: 'minor' | 'moderate' | 'severe';
  description: string;
  location?: string; // Where in the image
}

export interface QualityCheckOptions {
  entityType: string;
  expectedContent: string; // What should be in the image
  strictMode?: boolean; // Stricter checking (default: false)
  checkForText?: boolean; // Specifically check for unwanted text (default: true)
}

/**
 * Lightweight quality checker for generated images
 * Uses GPT-4o-mini with vision (cheap and fast)
 */
export class ImageQualityChecker {
  private client: OpenAI;
  private model = 'gpt-4o-mini'; // Lightweight model with vision

  constructor(apiKey?: string) {
    this.client = new OpenAI({
      apiKey: apiKey || process.env.OPENAI_API_KEY,
    });
  }

  /**
   * Check image quality
   */
  async checkImage(
    imageUrl: string,
    options: QualityCheckOptions
  ): Promise<QualityCheckResult> {
    const prompt = this.buildCheckPrompt(options);

    try {
      const response = await this.client.chat.completions.create({
        model: this.model,
        messages: [
          {
            role: 'system',
            content: 'You are a professional quality control specialist for AI-generated game art. Your job is to identify visual artifacts, anatomical issues, proportion problems, unwanted text, and other quality issues. Be concise and objective.',
          },
          {
            role: 'user',
            content: [
              {
                type: 'text',
                text: prompt,
              },
              {
                type: 'image_url',
                image_url: {
                  url: imageUrl,
                },
              },
            ],
          },
        ],
        response_format: { type: 'json_object' },
        max_tokens: 500, // Keep it short and cheap
        temperature: 0.3, // Low temperature for consistent checking
      });

      const result = JSON.parse(response.choices[0].message.content || '{}');

      return this.parseCheckResult(result, options);
    } catch (error) {
      console.error('Quality check failed:', error);
      // On error, default to manual review
      return {
        passed: false,
        score: 50,
        issues: [],
        recommendation: 'manual_review',
        explanation: 'Quality check failed - requires manual review',
      };
    }
  }

  /**
   * Build the quality check prompt
   */
  private buildCheckPrompt(options: QualityCheckOptions): string {
    const { entityType, expectedContent, strictMode, checkForText } = options;

    const parts: string[] = [
      `Analyze this ${entityType} image that should depict: ${expectedContent}`,
      '',
      'Check for the following issues:',
      '1. AI artifacts (weird textures, duplicate elements, fusion, melting)',
      '2. Anatomical problems (wrong proportions, extra/missing body parts)',
      '3. Distortions or blur in important areas',
    ];

    if (checkForText !== false) {
      parts.push('4. Unwanted text or letters in the image');
    }

    parts.push('5. Overall visual quality and coherence');

    if (strictMode) {
      parts.push('');
      parts.push('STRICT MODE: Be extra critical. Even minor issues should be flagged.');
    }

    parts.push('');
    parts.push('Respond with JSON in this format:');
    parts.push('{');
    parts.push('  "score": 0-100 (overall quality score),');
    parts.push('  "issues": [');
    parts.push('    {');
    parts.push('      "type": "artifact|anatomy|proportions|text|blur|distortion|other",');
    parts.push('      "severity": "minor|moderate|severe",');
    parts.push('      "description": "brief description",');
    parts.push('      "location": "where in the image"');
    parts.push('    }');
    parts.push('  ],');
    parts.push('  "explanation": "brief overall assessment"');
    parts.push('}');

    return parts.join('\n');
  }

  /**
   * Parse and interpret check result
   */
  private parseCheckResult(
    result: any,
    options: QualityCheckOptions
  ): QualityCheckResult {
    const score = result.score || 50;
    const issues: QualityIssue[] = (result.issues || []).map((issue: any) => ({
      type: issue.type || 'other',
      severity: issue.severity || 'moderate',
      description: issue.description || 'Unknown issue',
      location: issue.location,
    }));

    // Determine if passed
    const threshold = options.strictMode ? 85 : 70;
    const passed = score >= threshold && issues.filter(i => i.severity === 'severe').length === 0;

    // Determine recommendation
    let recommendation: 'approve' | 'regenerate' | 'manual_review';

    if (passed) {
      recommendation = 'approve';
    } else if (score < 50 || issues.filter(i => i.severity === 'severe').length > 0) {
      recommendation = 'regenerate';
    } else {
      recommendation = 'manual_review';
    }

    return {
      passed,
      score,
      issues,
      recommendation,
      explanation: result.explanation || 'No explanation provided',
    };
  }

  /**
   * Batch check multiple images
   */
  async checkImages(
    images: Array<{ url: string; options: QualityCheckOptions }>
  ): Promise<QualityCheckResult[]> {
    const results: QualityCheckResult[] = [];

    for (const { url, options } of images) {
      const result = await this.checkImage(url, options);
      results.push(result);
    }

    return results;
  }

  /**
   * Quick check (returns just pass/fail)
   */
  async quickCheck(
    imageUrl: string,
    expectedContent: string
  ): Promise<boolean> {
    const result = await this.checkImage(imageUrl, {
      entityType: 'image',
      expectedContent,
      strictMode: false,
    });

    return result.passed;
  }

  /**
   * Format check result for display
   */
  formatResult(result: QualityCheckResult): string {
    const lines: string[] = [];

    lines.push(`Quality Score: ${result.score}/100`);
    lines.push(`Status: ${result.passed ? '✅ PASSED' : '❌ FAILED'}`);
    lines.push(`Recommendation: ${result.recommendation.toUpperCase()}`);
    lines.push('');

    if (result.explanation) {
      lines.push(`Assessment: ${result.explanation}`);
      lines.push('');
    }

    if (result.issues.length > 0) {
      lines.push('Issues Found:');
      for (const issue of result.issues) {
        const emoji = {
          minor: '⚠️',
          moderate: '🟡',
          severe: '🔴',
        }[issue.severity];

        lines.push(`  ${emoji} ${issue.type.toUpperCase()}: ${issue.description}`);
        if (issue.location) {
          lines.push(`     Location: ${issue.location}`);
        }
      }
    } else {
      lines.push('No issues detected.');
    }

    return lines.join('\n');
  }
}

/**
 * Integration with image generation workflow
 */
export interface GenerateWithQCOptions {
  maxRetries?: number; // Max regeneration attempts (default: 3)
  autoApprove?: boolean; // Auto-approve if passed (default: false - requires user review)
  onQualityCheck?: (result: QualityCheckResult) => Promise<'approve' | 'regenerate' | 'abort'>;
}

/**
 * Generate image with automatic quality checking and retry
 */
export async function generateWithQualityControl(
  generateFn: () => Promise<{ url: string; prompt: string }>,
  checkOptions: QualityCheckOptions,
  qcOptions: GenerateWithQCOptions = {}
): Promise<{
  url: string;
  prompt: string;
  qualityCheck: QualityCheckResult;
  attempts: number;
}> {
  const maxRetries = qcOptions.maxRetries || 3;
  const checker = new ImageQualityChecker();

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    console.log(`\n🎨 Generation attempt ${attempt}/${maxRetries}...`);

    // Generate image
    const generated = await generateFn();

    console.log('✓ Image generated');
    console.log(`  URL: ${generated.url.substring(0, 60)}...`);

    // Quality check
    console.log('\n🔍 Running quality check...');
    const qualityCheck = await checker.checkImage(generated.url, checkOptions);

    console.log('\n' + checker.formatResult(qualityCheck));

    // Auto-approve if enabled and passed
    if (qcOptions.autoApprove && qualityCheck.passed) {
      console.log('\n✅ Auto-approved');
      return { ...generated, qualityCheck, attempts: attempt };
    }

    // User callback
    if (qcOptions.onQualityCheck) {
      const decision = await qcOptions.onQualityCheck(qualityCheck);

      if (decision === 'approve') {
        console.log('\n✅ Approved by user');
        return { ...generated, qualityCheck, attempts: attempt };
      } else if (decision === 'abort') {
        console.log('\n🛑 Aborted by user');
        throw new Error('Generation aborted by user');
      }
      // 'regenerate' continues to next attempt
    } else {
      // No callback, use recommendation
      if (qualityCheck.recommendation === 'approve') {
        console.log('\n✅ Passed quality check');
        return { ...generated, qualityCheck, attempts: attempt };
      } else if (qualityCheck.recommendation === 'manual_review') {
        console.log('\n⏸️  Requires manual review (returning for user approval)');
        return { ...generated, qualityCheck, attempts: attempt };
      }
    }

    // Regenerate
    if (attempt < maxRetries) {
      console.log(`\n🔄 Regenerating (${qualityCheck.recommendation})...`);
    } else {
      console.log('\n⚠️  Max retries reached, returning last attempt');
      return { ...generated, qualityCheck, attempts: attempt };
    }
  }

  throw new Error('Should not reach here');
}

// Global quality checker instance
export const globalQualityChecker = new ImageQualityChecker();
