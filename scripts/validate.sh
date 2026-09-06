#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

generated_path="$(find "$repo_root" \( -name .DS_Store -o -name '*.pyc' \) -print -quit)"
if [[ -n "$generated_path" ]]; then
  printf 'generated file must not be committed: %s\n' "$generated_path" >&2
  exit 1
fi

for skill in project-context-management skill-authoring; do
  test -f "$repo_root/skills/$skill/SKILL.md"
  grep -q '^name:' "$repo_root/skills/$skill/SKILL.md"
  grep -q '^description:' "$repo_root/skills/$skill/SKILL.md"
  test -f "$repo_root/skills/$skill/references/README.md"
done

if grep -R -n -E '(210122338617|i-[0-9a-f]{8,}|execute-api\.|@gmail\.com|personal-hermes-minimal)' \
  "$repo_root" --exclude='validate.sh'; then
  printf 'private deployment identifier detected\n' >&2
  exit 1
fi

ruby - "$repo_root" <<'RUBY'
require "pathname"
root = Pathname.new(ARGV.fetch(0))
errors = []
root.glob("**/*.md").sort.each do |file|
  file.read.scan(/\[[^\]]*\]\(([^)]+)\)/).flatten.each do |raw|
    target = raw.strip
    next if target.empty? || target.start_with?("http://", "https://", "mailto:", "#")
    target = target.split("#", 2).first
    next if target.empty?
    resolved = file.dirname.join(target).cleanpath
    errors << "#{file.relative_path_from(root)}: #{raw}" unless resolved.exist?
  end
end
abort(errors.join("\n")) unless errors.empty?
puts "markdown-relative-links-ok"
RUBY

printf 'hermes-context-kit validation passed\n'
