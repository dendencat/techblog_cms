let currentPage = 1;
const articlesPerPage = 6;
let articlesData = [];

// Fetch articles function
async function fetchArticles(page) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newArticles = Array.from({ length: articlesPerPage }, (_, i) => ({
        id: (page - 1) * articlesPerPage + i + 1,
        title: `記事タイトル ${(page - 1) * articlesPerPage + i + 1}`,
        excerpt: `これは記事 ${(page - 1) * articlesPerPage + i + 1} の概要です。`,
        link: '#'
      }));
      resolve(newArticles);
    }, 500);
  });
}

// Render articles
function renderArticles(articles) {
  const container = document.getElementById('articlesContainer');
  articles.forEach(article => {
    const card = document.createElement('div');
    card.className = 'article-card bg-white p-4 rounded shadow hover:shadow-lg transition';
    card.innerHTML = `
      <h3 class="text-lg font-bold text-gray-800 mb-2">${article.title}</h3>
      <p class="text-gray-600 mb-4">${article.excerpt}</p>
      <a href="${article.link}" class="text-blue-500 hover:underline">続きを読む</a>
    `;
    container.appendChild(card);
  });
}

// Search functionality
document.getElementById('searchBox')?.addEventListener('input', (e) => {
  const query = e.target.value.toLowerCase();
  const filteredArticles = articlesData.filter(article => 
    article.title.toLowerCase().includes(query) ||
    article.excerpt.toLowerCase().includes(query)
  );
  
  const container = document.getElementById('articlesContainer');
  container.innerHTML = '';
  renderArticles(filteredArticles);
});

// Infinite scroll
const observer = new IntersectionObserver(async (entries) => {
  if (entries[0].isIntersecting) {
    const newArticles = await fetchArticles(currentPage);
    articlesData = [...articlesData, ...newArticles];
    renderArticles(newArticles);
    currentPage++;
  }
}, {
  root: null,
  rootMargin: '100px',
  threshold: 0.1
});

// Start observation
document.addEventListener('DOMContentLoaded', () => {
  const sentinel = document.getElementById('scrollSentinel');
  if (sentinel) observer.observe(sentinel);
  fetchArticles(currentPage).then(articles => {
    articlesData = articles;
    renderArticles(articles);
    currentPage++;
  });
});
