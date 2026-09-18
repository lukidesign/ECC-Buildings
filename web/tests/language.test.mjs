import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import ts from 'typescript';
import { resolveLocale, translate, zh } from '../components/landscape/translations.ts';

for (const language of ['zh', 'zh-CN', 'zh-TW', 'zh-Hant-HK', 'ZH-cn', 'zh_SG']) {
  test(`Chinese browser preference: ${language}`, () => assert.equal(resolveLocale(null, language), 'zh'));
}
for (const language of ['en-US', 'fr-FR', 'ja-JP', '', 'zhuang']) {
  test(`English fallback: ${language}`, () => assert.equal(resolveLocale(null, language), 'en'));
}
test('saved choice takes precedence over browser', () => {
  assert.equal(resolveLocale('en', 'zh-CN'), 'en');
  assert.equal(resolveLocale('zh', 'en-US'), 'zh');
});
test('invalid saved value follows browser', () => assert.equal(resolveLocale('fr', 'zh-HK'), 'zh'));
test('all translations have both language values', () => {
  for (const [english, chinese] of Object.entries(zh)) {
    assert.ok(chinese.trim());
    assert.equal(translate('en', english), english);
    assert.equal(translate('zh', english), chinese);
  }
});
test('brand names retain their spelling', () => assert.equal(translate('zh', 'ECC'), 'ECC'));
test('all literal translation calls exist in the dictionary', () => {
  for (const file of ['landscape.tsx', 'panorama.tsx']) {
    const source = fs.readFileSync(new URL(`../components/landscape/${file}`, import.meta.url), 'utf8');
    const ast = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    function walk(node) {
      if (ts.isCallExpression(node) && node.expression.getText(ast) === 't' && ts.isStringLiteral(node.arguments[0])) {
        assert.ok(Object.hasOwn(zh, node.arguments[0].text), `Missing: ${node.arguments[0].text}`);
      }
      if (ts.isJsxText(node) && /[A-Za-z]{2}/.test(node.text)) {
        assert.ok(['ECC'].includes(node.text.trim()), `Untranslated JSX: ${node.text}`);
      }
      ts.forEachChild(node, walk);
    }
    walk(ast);
  }
});
