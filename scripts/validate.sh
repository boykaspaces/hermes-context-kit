#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

generated_path="$(find "$repo_root" -path "$repo_root/.git" -prune -o \
  \( -name .DS_Store -o -name '*.pyc' \) -print -quit)"
if [[ -n "$generated_path" ]]; then
  printf 'generated file must not be committed: %s\n' "$generated_path" >&2
  exit 1
fi

for skill in project-context-management multi-repo-system-management skill-authoring; do
  test -f "$repo_root/skills/$skill/SKILL.md"
  grep -q '^name:' "$repo_root/skills/$skill/SKILL.md"
  grep -q '^description:' "$repo_root/skills/$skill/SKILL.md"
  test -f "$repo_root/skills/$skill/references/README.md"
done

ruby - "$repo_root" <<'RUBY'
require "yaml"
root = File.expand_path(ARGV.fetch(0))
skills = Dir.glob(File.join(root, "skills", "*", "SKILL.md")).sort
skills.each do |path|
  text = File.read(path)
  abort("#{path}: frontmatter must start at byte 0") unless text.start_with?("---\n")
  parts = text.split(/^---\s*$\n/, 3)
  abort("#{path}: malformed frontmatter") unless parts.length == 3
  data = YAML.safe_load(parts.fetch(1), permitted_classes: [], aliases: false)
  name = data.fetch("name")
  description = data.fetch("description")
  version = data.dig("metadata", "context-kit", "version")
  abort("#{path}: name differs from directory") unless name == File.basename(File.dirname(path))
  abort("#{path}: invalid skill name") unless name.match?(/\A[a-z0-9]+(?:-[a-z0-9]+)*\z/) && name.length <= 64
  abort("#{path}: description must be <= 60 characters and end with a period") unless description.length <= 60 && description.end_with?(".")
  abort("#{path}: invalid metadata.context-kit.version") unless version.to_s.match?(/\A\d+\.\d+\.\d+\z/)
  related = data.dig("metadata", "context-kit", "related_skills") || []
  abort("#{path}: related_skills must be a list") unless related.is_a?(Array)
  abort("#{path}: invalid related skill name") unless related.all? { |related_name| related_name.match?(/\A[a-z0-9]+(?:-[a-z0-9]+)*\z/) }
end
puts "context-kit-skill-metadata-ok"
RUBY

ruby - "$repo_root" <<'RUBY'
root = File.expand_path(ARGV.fetch(0))
portable_roots = [
  File.join(root, "skills", "project-context-management"),
  File.join(root, "skills", "skill-authoring")
]
forbidden = [
  "/workspace",
  "hermes-default",
  "/home/hermes/.hermes/skills",
  "~/.hermes/skills",
  "SOUL.md",
  "AGENTS.md",
  "metadata.hermes",
  "Hermes"
]
portable_roots.each do |portable_root|
  Dir.glob(File.join(portable_root, "**", "*")).sort.each do |path|
    next unless File.file?(path)
    text = File.read(path)
    forbidden.each do |value|
      abort("#{path}: deployment-specific value is not portable: #{value}") if text.include?(value)
    end
  end
end

puts "deployment-portability-ok"
RUBY

python3 "$repo_root/skills/multi-repo-system-management/scripts/validate_multi_repo_context.py" \
  --help >/dev/null
python3 "$repo_root/scripts/context_kit.py" --help >/dev/null
python3 -m json.tool \
  "$repo_root/skills/multi-repo-system-management/templates/system-task.json" >/dev/null
python3 -m json.tool \
  "$repo_root/skills/multi-repo-system-management/templates/component-handoff.json" >/dev/null
python3 "$repo_root/skills/multi-repo-system-management/scripts/validate_multi_repo_context.py" \
  repository --root "$repo_root"
python3 "$repo_root/scripts/context_kit.py" validate --root "$repo_root"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s "$repo_root/skills/multi-repo-system-management/tests" \
  -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s "$repo_root/tests" \
  -p 'test_*.py'

for artifact in "$repo_root"/schemas/*.json "$repo_root"/profiles/*/profile.json \
  "$repo_root"/adapters/runtime/*/adapter.json \
  "$repo_root"/adapters/workflow/*/adapter.json; do
  python3 -m json.tool "$artifact" >/dev/null
done

if grep -R -n -E '(210122338617|i-[0-9a-f]{8,}|execute-api\.|@gmail\.com|personal-hermes-minimal)' \
  "$repo_root" --exclude-dir='.git' --exclude='validate.sh'; then
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

printf 'context-kit validation passed\n'
