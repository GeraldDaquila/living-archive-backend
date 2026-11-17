(function () {
	'use strict';

	function init(root) {
		if (root.getAttribute('data-mini-use-initialized') === '1') return;
		var form = root.querySelector('.mini-use-form');
		var input = root.querySelector('.mini-use-query');
		var button = root.querySelector('.mini-use-submit');
		var label = root.querySelector('.mini-use-submit-label');
		var status = root.querySelector('.mini-use-status');
		var results = root.querySelector('.mini-use-results');
		var endpoint = root.getAttribute('data-endpoint');

		if (!form || !input || !button || !label || !status || !results || !endpoint) return;
		root.setAttribute('data-mini-use-initialized', '1');

		// USE specialist handoff adapter: when The Guide opens the Catalogue
		// with a bounded visitor question, seed the existing native form and
		// submit it through Mini-USE's own /navigate contract. No duplicate
		// retrieval or ranking is performed here.
		var handoffQuery = '';
		try {
			var params = new URLSearchParams(window.location.search);
			handoffQuery = (params.get('catalogue_query') || '').trim();
			if (handoffQuery) {
				params.delete('catalogue_query');
				var cleanQuery = window.location.pathname + (params.toString() ? '?' + params.toString() : '') + window.location.hash;
				history.replaceState(null, document.title, cleanQuery);
			}
		} catch (e) {}

		form.addEventListener('submit', function (event) {
			event.preventDefault();
			var query = input.value.trim();

			if (!query) {
				status.textContent = 'Please enter a question.';
				input.focus();
				return;
			}

			button.disabled = true;
			button.classList.add('is-loading');
			label.textContent = 'Exploring…';
			status.textContent = 'Looking through the catalogue…';
			results.hidden = true;
			results.replaceChildren();

			fetch(endpoint, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ query: query })
			}).then(function (response) {
				return response.json().then(function (data) {
					if (!response.ok) throw new Error(data.message || 'We couldn’t find a result just now. Please try again.');
					return data;
				});
			}).then(function (data) {
				status.textContent = '';
				results.replaceChildren();
				if (data.synthesis) {
					var synthesis = document.createElement('div');
					synthesis.className = 'mini-use-synthesis';
					var synthesisText = document.createElement('p');
					synthesisText.textContent = String(data.synthesis);
					synthesis.appendChild(synthesisText);
					results.appendChild(synthesis);
				}

				var doors = Array.isArray(data.doors) ? data.doors : [];
				var helper = window.LivingArchiveAnswerDoorway;
				var doorContainer = document.createElement('div');
				doorContainer.className = 'mini-use-doors';
				var items = doors.map(function (door) {
					return {
						title: door && door.title,
						url: door && door.canonical_url,
						rationale: door && (door.why_this_may_help || door.description || ''),
						kind: 'continue'
					};
				});
				var count = helper && typeof helper.renderMany === 'function'
					? helper.renderMany(doorContainer, items)
					: 0;
				if (count) results.appendChild(doorContainer);
				if (!count) {
					var noMatch = document.createElement('p');
					noMatch.textContent = 'We couldn’t find a close match this time. Try describing the situation a little differently.';
					results.appendChild(noMatch);
				}
				results.hidden = false;
			}).catch(function (error) {
				status.textContent = error.message || 'Something went wrong. Please try again.';
				results.hidden = true;
			}).finally(function () {
				button.disabled = false;
				button.classList.remove('is-loading');
				label.textContent = 'Explore the Catalogue';
			});
		});
		if (handoffQuery) {
			input.value = handoffQuery;
			setTimeout(function () {
				if (typeof form.requestSubmit === 'function') form.requestSubmit();
				else button.click();
			}, 0);
		}
	}

	window.MiniUsePlugin = { init: init };
	document.addEventListener('DOMContentLoaded', function () {
		document.querySelectorAll('.mini-use-plugin').forEach(init);
	});
})();
